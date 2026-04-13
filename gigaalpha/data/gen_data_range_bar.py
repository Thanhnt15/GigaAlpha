import pandas as pd
import pickle
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

logger = logging.getLogger(__name__)

def get_tick_data(day_start: str, day_end: str):
    # MongoDB connection details from environment variables
    mongo_host = os.getenv('MONGO_HOST')
    mongo_port = os.getenv('MONGO_PORT')
    mongo_user = os.getenv('MONGO_USER')
    mongo_pass = os.getenv('MONGO_PASS')
    mongo_auth = os.getenv('MONGO_AUTH_SOURCE', 'admin')
    mongo_db   = os.getenv('MONGO_DB_NAME')

    if not all([mongo_host, mongo_port, mongo_user, mongo_pass, mongo_db]):
        logger.error("Missing MongoDB configuration in environment variables (.env)")
        raise ValueError("Please set MONGO_HOST, MONGO_PORT, MONGO_USER, MONGO_PASS, and MONGO_DB_NAME in your .env file.")

    client = MongoClient(
        host=mongo_host,
        port=int(mongo_port),
        username=mongo_user,
        password=mongo_pass,
        authSource=mongo_auth,
        connectTimeoutMS=30000,         
        socketTimeoutMS=None,            
        serverSelectionTimeoutMS=30000
    )
    db = client[mongo_db]
    all_collections = db.list_collection_names()
    db_days = sorted(name[:10] for name in all_collections if 'tickdata' in name)
  
    target_days = [day for day in db_days if day_start <= day <= day_end]

    df_all = []
    for day in target_days:
        logger.info(f"Downloading data for: {day}")
        df_day = pd.DataFrame(db[f'{day}_busd_ps_tickdata'].find({},{'_id': 0}))
        df_all.append(df_day)
    final_df = pd.concat(df_all, ignore_index=True)
    return final_df

def gen_range_bar(df_tick: pd.DataFrame, threshold: float):
    dt_full = pd.to_datetime(df_tick['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Ho_Chi_Minh')

    df_tick = df_tick[dt_full.dt.time >= pd.to_datetime('09:00:00').time()].copy()
    
    df_tick['curr_date_ref'] = pd.to_datetime(df_tick['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Ho_Chi_Minh').dt.date
    
    candles = []
    
    curr_o = None
    curr_h = -float('inf')
    curr_l = float('inf')
    curr_c = None
    curr_vol_acc = 0
    curr_t_open = None
    curr_day = None

    for i in range(len(df_tick)):
        tick = df_tick.iloc[i]
        p = tick['last']
        v = tick['matchedVolume']
        t = tick['timestamp']
        d = tick['curr_date_ref']

        if curr_o is None or d != curr_day:
            if curr_o is not None and d != curr_day:
                candles.append({
                    't_open': curr_t_open, 
                    't_close': df_tick['timestamp'].iloc[i-1], 
                    'open': curr_o, 'high': curr_h, 'low': curr_l, 'close': curr_c, 
                    'matchedVolume': curr_vol_acc
                })
                curr_vol_acc = 0

            curr_o = curr_h = curr_l = curr_c = p
            curr_vol_acc = v
            curr_t_open = t
            curr_day = d
            continue

        curr_h = max(curr_h, p)
        curr_l = min(curr_l, p)
        curr_c = p
        curr_vol_acc += v

        if (curr_h - curr_l) >= threshold:
            candles.append({
                't_open': curr_t_open,
                't_close': t,
                'open': curr_o,
                'high': curr_h, 
                'low': curr_l, 
                'close': curr_c,
                'matchedVolume': curr_vol_acc
            })
            
            curr_o = None
            curr_vol_acc = 0

    if curr_o is not None:
        candles.append({
            't_open': curr_t_open, 
            't_close': df_tick['timestamp'].iloc[-1],
            'open': curr_o, 'high': curr_h, 'low': curr_l, 'close': curr_c, 
            'matchedVolume': curr_vol_acc
        })

    df = pd.DataFrame(candles)

    def to_dt(s): 
        return pd.to_datetime(s, unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Ho_Chi_Minh').dt.tz_localize(None)

    # Note: df['dt_open'] cần được tạo trước khi sử dụng floor('s')
    df['dt_open'] = to_dt(df['t_open'])
    df['timestamp'] = df['dt_open'].dt.floor('s')
    df['day'] = df['dt_open'].dt.strftime('%Y_%m_%d')
    df['timeFirst'] = df['dt_open'].dt.strftime('%H:%M:%S')
    df['timeLast'] = to_dt(df['t_close']).dt.strftime('%H:%M:%S')
    
    df['totalMatchVolume'] = df.groupby('day')['matchedVolume'].cumsum()

    # Execution Time
    df['executionTime'] = df.groupby('day')['timeFirst'].shift(-1).fillna('14:45:00')
    df.loc[df['executionTime'] > '14:45:00', 'executionTime'] = '14:45:00'

    # Logic Session
    df['executable'] = True
    df['session'] = 'NaN'
    
    # 1. Lunch
    flt_lunch = (df['timeLast'] >= '11:30:00') & (df['timeLast'] < '13:00:00') & \
                (df['executionTime'] > '11:30:00') & (df['executionTime'] < '13:00:00')
    df.loc[flt_lunch, ['executable', 'session']] = [False, 'lunch']

    # 2. preATC
    flt_pre_atc = (df['timeLast'] >= '14:30:00') & (df['timeLast'] < '14:45:00') & \
                  (df['executionTime'] > '14:30:00') & (df['executionTime'] < '14:45:00')
    df.loc[flt_pre_atc, ['executable', 'session']] = [False, 'preATC']

    # 3. unconditionalATC
    flt_atc = (df['timeLast'] >= '14:45:00') & (df['executionTime'] >= '14:45:00')
    df.loc[flt_atc, ['executable', 'session', 'executionTime']] = [True, 'unconditionalATC', '14:45:00']

    df.loc[df['executionTime'] == '14:30:00', 'executable'] = False

    # Giá Entry/Exit
    df['entryPrice'] = df.groupby('day')['open'].shift(-1)
    df.loc[df['session'] == 'unconditionalATC', 'entryPrice'] = df['close']
    df['exitPrice'] = df.groupby('day')['entryPrice'].shift(-1)
    df['priceChange'] = df['exitPrice'] - df['entryPrice']

    cols = ['timestamp','day','open','high','low','close','matchedVolume','totalMatchVolume',
            'timeFirst','timeLast','executionTime','executable','session','entryPrice','exitPrice','priceChange']
    return df[cols]

if __name__ == '__main__':
    DIC_RANGE_PATH = Path('data/dic_range_bar.pickle')
    DIC_RANGE_BAR = {}
    LST_THRESHOLD = [5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0]
    df_tick = get_tick_data(
        day_start='2022_02_07',
        day_end='2026_04_01'
    )
    for threshold in LST_THRESHOLD:
        logger.info(f"Generating range bars for threshold: {threshold}")
        df = gen_range_bar(df_tick,threshold)
        DIC_RANGE_BAR[threshold] = df
    with open(DIC_RANGE_PATH,'wb') as f:
        pickle.dump(DIC_RANGE_BAR,f)
    logger.info("Data generation process completed.")
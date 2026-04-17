import numpy as np
import pandas as pd
import logging
from datetime import datetime
from scipy.stats import skew, kurtosis
from math import erf, sqrt
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AlphaDomains:
    @staticmethod
    def adjust_positions(df):
        pos = df['position'].copy()
        flt_unexecutable = ~df['executable']
        pos.loc[flt_unexecutable] = np.nan
        flt_atc = df['executionTime'] == '14:45:00'
        pos.loc[flt_atc] = 0
        pos = pos.ffill().fillna(0)
        return pos
            
    @staticmethod
    def compute_action_tvr_and_fee(df, fee):
        df['action'] = df['position'].diff(1).fillna(df['position'].iloc[0])
        df['turnover'] = df['action'].abs()
        df['fee'] = df['turnover'] * fee
 
    @staticmethod
    def compute_profits(df):
        df['grossProfit'] = df['position'] * df['priceChange']
        df['cumGrossProfit'] = df['grossProfit'].cumsum()
        df['netProfit'] = df['grossProfit'] - df['fee']
        df['cumNetProfit'] = df['netProfit'].cumsum()
    
    @staticmethod
    def calculate_working_days(start, end, workdays_per_year: int = 250) -> int:
        """
        Tính số ngày làm việc từ start đến end, với chuẩn workdays_per_year.
        """
        if isinstance(start, int):
            start_date = datetime.strptime(str(start), "%Y%m%d")
            end_date = datetime.strptime(str(end), "%Y%m%d")
        else:
            start_date = datetime.strptime(start, "%Y_%m_%d")
            end_date = datetime.strptime(end, "%Y_%m_%d")

        total_days = (end_date - start_date).days
        working_days = total_days * workdays_per_year / 365.0
        return round(working_days)
    
    @staticmethod
    def aggregate_to_1d(df):
        agg_dict = {
            "turnover": "sum",
            "netProfit": "sum",
        }
        if "booksize" in df.columns:
            agg_dict["booksize"] = "last"
        return df.groupby('day').agg(agg_dict)

    @staticmethod
    def compute_performance(df_1d, start=None, end=None, equity=300):
        try:
            if start is not None:
                df_1d = df_1d[df_1d.index >= start]
            if end is not None:
                df_1d = df_1d[df_1d.index <= end]

            df_1d = df_1d.copy()
            df_1d['cumnet'] = df_1d['netProfit'].cumsum()

            try:
                mean = df_1d["netProfit"].mean()
                std = df_1d["netProfit"].std()

                if std and not np.isnan(std):
                    working_days = AlphaDomains.calculate_working_days(start, end)
                    sharpe = mean / std * (working_days ** 0.5)
                    daily_sharpe = mean / std
                else:
                    sharpe = np.nan
                    daily_sharpe = np.nan
            except:
                sharpe = -999
                daily_sharpe = np.nan

            tvr = df_1d['turnover'].mean()
            ppc = df_1d['netProfit'].sum() / (df_1d['turnover'].sum() + 1e-8)
            
            mdd, mdd_pct, cdd, cdd_pct = AlphaDomains.compute_mdd_vectorized(df_1d, equity)
            returns = df_1d['netProfit'] / equity
            
            winning_profits = df_1d[df_1d['netProfit'] > 0]['netProfit']
            total_profit = winning_profits.sum()
            hhi = ((winning_profits / (total_profit + 1e-9)) ** 2).sum()

            new_report = {
                'sharpe': round(sharpe, 3),
                "hhi": round(hhi, 3),
                "psr": round(AlphaDomains.dsr(returns, daily_sharpe, 0), 3),
                "dsr": round(AlphaDomains.dsr(returns, daily_sharpe), 3),
                'mdd': round(mdd, 3),
                'mddPct': round(mdd_pct.iloc[-1], 4),
                'cdd': round(cdd, 3),
                'cddPct': round(cdd_pct.iloc[-1], 4),
                'ppc': round(ppc, 4),
                'tvr': round(tvr, 4),
                'start': df_1d.index[0],
                'end': df_1d.index[-1],
                'lastProfit': round(df_1d['netProfit'].iloc[-1], 2),
                "netProfit": round(df_1d['netProfit'].sum(), 2),
                "profitPct": round(df_1d['netProfit'].sum(), 2) / equity * 100,
            }
            return new_report
        except Exception as e:
            logger.error(f"Error in compute_performance: {str(e)}")
            return {}
    
    @staticmethod
    def compute_mdd_vectorized(df_1d, equity=300):
        if 'cumNetProfit' in df_1d:
            net_profit = df_1d['cumNetProfit']
        else:
            net_profit = df_1d['netProfit'].cumsum()

        cummax = net_profit.cummax()
        cdd = cummax - net_profit
        cdd_pct = (cdd / (equity + cummax) * 100)

        mdd = cdd.cummax().iloc[-1]
        mdd_pct = cdd_pct.cummax()
        cdd_last = cdd.iloc[-1]

        return mdd, mdd_pct, cdd_last, cdd_pct

    @staticmethod
    def dsr(returns, sharpe, sr_benchmark=0.18):
        try:
            if np.isnan(sharpe): return 0
            def volatility_sharpe(returns):
                sample_size = len(returns)
                skewness = skew(returns)
                _kurtosis = kurtosis(returns, fisher=True, bias=False)
                return np.sqrt((1 - skewness*sharpe + (_kurtosis + 2)/4*sharpe**2) / (sample_size - 1)), sharpe
            
            sigma_sr, sr = volatility_sharpe(returns)
            z = (sr - sr_benchmark) / (sigma_sr + 1e-9)
            return 0.5 * (1 + erf(z / sqrt(2))) * 100
        except:
            return 0

    @staticmethod
    def apply_cut_time(DIC_FREQS: Dict[Any, pd.DataFrame], cut_time: str = '14:25:00'):
        df_1m = DIC_FREQS[1]
        df_1m = df_1m[df_1m['executionTime'] >= cut_time]
        dict_cut_price = df_1m.groupby("day")['entryPrice'].first().to_dict()
        for freq in DIC_FREQS.keys():
            df = DIC_FREQS[freq].copy()
            df['price_at_cutTime'] = df['day'].map(dict_cut_price)
        
            df.loc[df['executionTime'] >= cut_time, 'entryPrice'] = df['price_at_cutTime']
            df['exitPrice'] = df['entryPrice'].shift(-1)
            df['priceChange'] = df['exitPrice'] - df['entryPrice']
            df.loc[df['executionTime'] == '14:45:00', 'priceChange'] = 0
            
            DIC_FREQS[freq] = df
        return DIC_FREQS


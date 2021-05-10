from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
import pandas as pd
from datetime import datetime
import baostock as bs
import numpy as np


@dataclass
class StockInfo:
    data: pd.DataFrame = field(default_factory=list)
    portfolio: Dict[str, int] = field(default_factory=list)

    def __init__(
        self,
        portfolio: Dict[str, int],
        data=None,
    ):
        self.portfolio = portfolio
        self.data = data
        bs.login()
        # print("login respond  error_msg:" + self.loginStatus.error_msg)

    def logout(self) -> None:
        bs.logout()
        return

    def fetchStocksData(
        self,
        start_date: str,
        end_date: str,
        stock_codes: List[str] = None,
        freq: str = "m",
        vars: List[str] = [
            "date",
            "code",
            # "open",
            "close",
            "pctChg",
            "volume",
            "amount",
        ],
    ) -> pd.DataFrame:

        if not stock_codes:
            stock_codes = self.portfolio.keys()

        dfs = []
        for stock_code in stock_codes:

            rs = bs.query_history_k_data_plus(
                stock_code,
                ",".join(vars),
                # 'date,code,close,pctChg,volume,amount',
                start_date=start_date,
                end_date=end_date,
                frequency=freq,
                adjustflag="1",
            )
            print(
                f"fetching stock return data for {stock_code} from {start_date} to {end_date}..."
            )
            df = rs.get_data()
            for column in df.columns:
                df[column] = pd.to_numeric(df[column], errors="ignore")
            dfs.append(df)

        if len(dfs) > 0:
            self.data = pd.concat(dfs)

        return self.data

    def calcStockHPR(
        self,
        stock_ex_code: str,
    ) -> float:

        df = self.data[self.data.code == stock_ex_code].loc[:, ["pctChg"]]

        mthly_returns = np.array(df)

        if mthly_returns.__len__() == 0:
            return 0

        return np.prod(mthly_returns / 100 + 1) - 1

    def calcPortfolioValue(
        self, portfolio: Dict[str, float] = None, start: bool = True
    ) -> float:
        if not portfolio:
            portfolio = self.portfolio

        if self.data.empty:
            print("No stock data has been fetched. Run fetchStocksData first.")
            return 0

        df = self.data
        dates = sorted(df.date.unique())
        target_date = dates[0] if start else dates[-1]

        val = 0

        for stock, shares in portfolio.items():
            ser = df[(df.date == target_date) & (df.code == stock)]
            if not ser.empty:
                adj = 1 / (1 + float(ser.pctChg) / 100) if start else 1
                val += float(ser.close) * adj * shares

        return val

    def calcPortfolioReturn(
        self,
        portfolio: Dict[str, float] = None,
    ) -> float:
        if not portfolio:
            portfolio = self.portfolio

        if self.data.empty:
            print("No stock data has been fetched. Run fetchStocksData first.")
            return 0

        start_val = self.calcPortfolioValue(portfolio=portfolio, start=True)
        end_val = self.calcPortfolioValue(portfolio=portfolio, start=False)

        if start_val == 0:
            print("starting portfolio value is zero. No return is calculated.")
            return 0
        else:
            return (end_val / start_val) - 1


if __name__ == "__main__":
    stock_info = StockInfo()
    start = "2021-1-1"
    end = "2021-4-1"
    df = pd.read_csv("./Datasets/unit-fund/holdings_change_21q1.csv")
    df.sort_values(by="mkt_val_21q1", ascending=False, inplace=True)

    df = df.head(50)
    df["return_q1"] = df.apply(
        lambda row: stock_info.calcStockHPR(start, end, row["stock_ex_code"]), axis=1
    )

    df.to_csv("./Datasets/unit-fund/major_holdings_21q1.csv", index=False)

    stock_info.logout()

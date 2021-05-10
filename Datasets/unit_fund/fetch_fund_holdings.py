import pandas as pd
from bs4 import BeautifulSoup
import requests
from typing import List, Tuple
from dataclasses import dataclass, field
import json


@dataclass
class FundHoldings:

    years: List[int]
    funds: pd.DataFrame = field(default_factory=list)

    def fetch_holdings(self, fund_code: str, year: int) -> pd.DataFrame:
        url = (
            "http://fundf10.eastmoney.com/"
            f"FundArchivesDatas.aspx?type=jjcc&code={fund_code}"
            f"&topline=10&year={year}&month="
        )
        doc = requests.get(url).text
        try:
            dfs = pd.read_html(
                doc,
                # dtype=str,
                encoding="UTF-8",
                converters={"股票代码": str},
            )

            num_qtrs = len(dfs)
            qtrs = [f"{year}Q{i+1}" for i in range(num_qtrs)]

            # rename the columns
            # if it's current year, need to drop useless columns
            for i, df in enumerate(dfs):
                if df.shape[1] == 9:
                    df.drop(["最新价", "涨跌幅"], axis=1, inplace=True)

                df.drop(["相关资讯"], axis=1, inplace=True)

                # print(df.shape)
                df.columns = [
                    "rank",
                    "stock_code",
                    "stock_name",
                    "pct",
                    "shares",
                    "mkt_val",
                ]
                df.insert(0, "period", qtrs[i])
                df.insert(0, "fund_code", fund_code)

            results = pd.concat(dfs, ignore_index=True)

        except:
            print(
                f"Failed: fetching {fund_code} in year {year}. Data is not available."
            )
            results = None
        return results

    def get_fund_list(self) -> List[str]:

        url = "http://fund.eastmoney.com/js/fundcode_search.js"
        doc = requests.get(url).text

        obj = doc[doc.find("[") : doc.rfind("]") + 1]
        json_file = json.loads(obj)

        df = pd.DataFrame(
            json_file,
            columns=["fund_code", "short_name", "name", "fund_type", "full_name"],
        )

        self.funds = df[df.fund_type == "股票型"].loc[:, ["fund_code", "name"]]

        return df

    def fetch_all_holdings(
        self, funds: List[str] = [], years: List[int] = []
    ) -> pd.DataFrame:
        dfs = []
        if funds == []:
            funds = self.funds.fund_code

        if years == []:
            years = self.years

        for fund in funds:
            for year in years:
                print(f"fetching results for {fund} in year {year}")
                dfs.append(self.fetch_holdings(fund, year))

        return pd.concat(dfs, ignore_index=True)


if __name__ == "__main__":

    # use the FundHoldings class to fetch the fund holdings data
    # data source: eastmoney.com

    # attemp = FundHoldings([2021, 2020])
    # attemp.get_fund_list().to_csv(".\\Datasets\\unit-fund\\fund_list.csv")
    # attemp.fetch_all_holdings().to_csv(".\\Datasets\\unit-fund\\all_holdings.csv")

    # data processing
    df = pd.read_csv(".\\Datasets\\unit-fund\\all_holdings.csv")
    cap_21q1 = (
        df[df.period == "2021Q1"]
        .groupby(["stock_code", "stock_name"])
        .sum()
        .mkt_val.sort_values(ascending=False)
    )
    cap_21q1 = (cap_21q1) / cap_21q1.sum()
    cap_20q4 = (
        df[df.period == "2020Q4"]
        .groupby(["stock_code", "stock_name"])
        .sum()
        .mkt_val.sort_values(ascending=False)
    )

    cap_20q4 = (cap_20q4) / cap_20q4.sum()

    cap_change = cap_20q4.to_frame().join(
        cap_21q1.to_frame(), lsuffix="_20q4", rsuffix="_21q1"
    )
    cap_change["change"] = 100 * (cap_change.mkt_val_21q1 - cap_change.mkt_val_20q4)
    cap_change.sort_values(by="change", ascending=False, inplace=True)
    cap_change.reset_index(inplace=True)
    cap_change["stock_ex_code"] = cap_change.stock_code.apply(
        lambda x: f"sh.{x}"
        if len(f"{x}") == 6 and f"{x}"[0] == "6"
        else f"sz.{'0'*(6-len(f'{x}'))}{x}",
    )
    cap_change.to_csv("./Datasets/unit-fund/holdings_change_21q1.csv", index=False)

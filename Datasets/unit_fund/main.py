from fetch_stock_returns import StockInfo
import pandas as pd
import numpy as np

stocks = StockInfo(portfolio={})

meta_file = "./Datasets/unit_fund/holdings_change_21q1.csv"
meta_data = pd.read_csv(meta_file)
stock_codes = list(meta_data.stock_ex_code.unique())

# fetch stock data for all 760 stocks
stocks.fetchStocksData("2021-1-1", "2021-5-1", stock_codes=stock_codes)

stocks.data.to_csv("stock_data.csv", index=False)

# -------------------------- TO DO: replace the input with a Json file------------------------- #
myPortfolio = {"sh.601318": 100, "sh.600438": 200}
stocks.portfolio = myPortfolio
myReturn = stocks.calcPortfolioReturn()

print(myReturn)


# print(stock_codes)
# print(len(stock_codes))


# stocks = StockInfo(portfolio={"sh.601318": 100, "sh.600438": 200})

# print(stocks)

# df = stocks.fetchStocksData("2021-1-1", "2021-5-1")
# print(stocks.data)
# print(stocks.calcPortfolioValue())
# print(stocks.calcPortfolioValue(start=False))
# print(stocks.calcPortfolioReturn())
# print(stocks)
# print(df)
# print(stocks.calcStockHPR("sh.601318"))


stocks.logout()
# print(stocks.calcStockHPR("2021-1-1", "2021-4-1", "sh.601318"))

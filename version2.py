# code to generate Tax profile for 2018 and 2019 ( ignores BTC trades)
# Shreyank Shetty
# shreyankshetty14@gmail.com


import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta
# Assign spreadsheet filename to `file`
file = 'Assignment.xlsx'
# Load spreadsheet
xl = pd.ExcelFile(file)

# Load a sheet into a DataFrame by name: df1
df = xl.parse('Sheet1')

# add new column called isMatch to dataframe
length = (len(df.index))
boolList = []
for i in range(0, length):
    boolList.append(False)
df.insert(7, "isMatch", boolList)

# get list of unique stocks
uniqueStockSymbol = df.Symbol.unique()

shortTerm2018 = 0
longTerm2019 = 0
shortTerm2019 = 0


# define wash sale check
def washSaleCheck(df2, index, highestBuyIndex):
    washSale = False
    sellTradeDate = df2.loc[index, 'TradeDate']
    buyTradeDate = df2.loc[highestBuyIndex, 'TradeDate']
    lowerWashSaleDate = sellTradeDate - relativedelta(months=1)
    upperWashSaleDate = sellTradeDate + relativedelta(months=1)
    if (lowerWashSaleDate < buyTradeDate) and (upperWashSaleDate > buyTradeDate):
        for i, r in df2.iterrows():
            if (r['Txn'] == 'BUY'):
                tradeDate = r['TradeDate']
                if (tradeDate > sellTradeDate) and (tradeDate < buyTradeDate):
                    washSale = True
    return washSale


# define function to get higest buy trade before the sell:
def findHighestBuy(df2, index):
    highestTradePrice = 0
    highestBuyIndex = 0
    for i, r in df2.iterrows():
        # check that trade is a buy and weather its already matched or not
        if (r['Txn'] == 'BUY') and (r['isMatch'] == False):
            # check that the trade happened before the sell and also if the  trade price is higest
            if (r['Quantity'] > 0):
                if (i > index) and (r['TradePrice'] > highestTradePrice):
                    washSale = washSaleCheck(df2, index, i)
                    if washSale == False:
                        highestTradePrice = r['TradePrice']
                        highestBuyIndex = i
    # return the index of higest buy order before the sell happened
    return highestBuyIndex


# define function to get higest long term buy orders.
def findLongTermBuy(df2, index):
    highestLongTradePrice = 0
    highestLongBuyIndex = 0
    sellTradeDate = df2.loc[index, 'TradeDate']
    # set longtermdate as sell order date minus one year
    longTermDate = sellTradeDate - relativedelta(years=1)
    for i, r in df2.iterrows():
        # check if buy date less than longtermdate and if buy happened before sell
        if (r['TradeDate'] < longTermDate) and (i > index):
            # check if trade is buy and if its not matched before
            if (r['Txn'] == 'BUY') and (r['isMatch'] == False):
                if (r['TradePrice'] > highestLongTradePrice) and (r['Quantity'] > 0):
                    highestLongTradePrice = r['TradePrice']
                    highestLongBuyIndex = i
    # if there is a long trade then return index of buy
    if highestLongTradePrice > 0:
        return highestLongBuyIndex
    # return none if no long buy matched.
    else:
        return None


# define recursive algorithm to match sell order with all buys uptil that point(date)
def recursiveMatchAlgo2018(df2, index, quantity, shortTermGain2018):
    if quantity == 0:
        return shortTermGain2018
    else:
        highestBuyIndex = findHighestBuy(df2, index)
        if highestBuyIndex == 0:
            quantity = 0
            return recursiveMatchAlgo2018(df2, index, quantity, shortTermGain2018)

        # check if buy quanity is less that sell order
        if (quantity > df2.loc[highestBuyIndex, 'Quantity']):
            # calculate the gains/losses from trade.
            sGain = ((df2.loc[index, 'TradePrice'])*(df2.loc[highestBuyIndex, 'Quantity']) - (
                df2.loc[highestBuyIndex, 'TradePrice'])*(df2.loc[highestBuyIndex, 'Quantity']))
            # cumulative add the short term gains/losses
            shortTermGain2018 = shortTermGain2018 + sGain
            # reduce quantity by the quantity of trade matched
            quantity = quantity - (df2.loc[highestBuyIndex, 'Quantity'])
            # update dataframe to mark buy trade as matched
            df2.at[highestBuyIndex, 'isMatch'] = True
            df.at[highestBuyIndex, 'isMatch'] = True
        # if buy order quantity is more than sell quantity
        else:
            # calculate short term gain for the trade matched
            shortTermGain2018 = shortTermGain2018 + (((df2.loc[index, 'TradePrice'])*quantity) - (
                (df2.loc[highestBuyIndex, 'TradePrice'])*quantity))
            # update buy order quantity. reduce by number of quantity matched
            df2.at[highestBuyIndex, 'Quantity'] = df2.loc[highestBuyIndex,
                                                          'Quantity'] - quantity
            df.at[highestBuyIndex, 'Quantity'] = df.loc[highestBuyIndex,
                                                        'Quantity'] - quantity
            # update sell order as Matched
            df2.at[index, 'isMatch'] = True
            df.at[index, 'isMatch'] = True
            quantity = 0
        return recursiveMatchAlgo2018(df2, index, quantity, shortTermGain2018)


# define recursive algo for computing gains for 2019
def recursiveMatchAlgo2019(df2, index, quantity, longTermGain, shortTermGain):
    if quantity == 0:
        return shortTermGain, longTermGain
    else:
        # get the long buy
        longTermBuyIndex = findLongTermBuy(df2, index)
        # execute algo for long buy exists.
        if longTermBuyIndex != None:
            # if sell quantity greater than buy quantity
            if quantity > df2.loc[longTermBuyIndex, 'Quantity']:
                # calculate the long term gains/losses
                gain = ((df2.loc[index, 'TradePrice'])*(df2.loc[longTermBuyIndex, 'Quantity']) - (
                    df2.loc[longTermBuyIndex, 'TradePrice'])*(df2.loc[longTermBuyIndex, 'Quantity']))
                # cumulative add the long term gains/losses
                longTermGain = longTermGain + gain
                # update the quantity and buy trades in the dataframe
                quantity = quantity - (df2.loc[longTermBuyIndex, 'Quantity'])
                df2.at[longTermBuyIndex, 'isMatch'] = True
                df.at[longTermBuyIndex, 'isMatch'] = True
            else:
                # calculate the long term gains/losses
                longTermGain = longTermGain + (((df2.loc[index, 'TradePrice'])*quantity) - (
                    (df2.loc[longTermBuyIndex, 'TradePrice'])*quantity))
                # update the dataframe
                df2.at[longTermBuyIndex, 'Quantity'] = (
                    df2.loc[longTermBuyIndex, 'Quantity']) - quantity
                df.at[longTermBuyIndex, 'Quantity'] = (
                    df.loc[longTermBuyIndex, 'Quantity']) - quantity
                df2.at[index, 'isMatch'] = True
                df.at[index, 'isMatch'] = True
                quantity = 0
            return recursiveMatchAlgo2019(df2, index, quantity, longTermGain, shortTermGain)
        else:
            # exceute algo for no long buy
            # get the higest buy price that was exceuted before this sell
            highestBuyIndex = findHighestBuy(df2, index)
            if highestBuyIndex == 0:
                quantity = 0
                return recursiveMatchAlgo2019(df2, index, quantity, longTermGain, shortTermGain)
            # check if buy quanity is less that sell order
            if (quantity > df2.loc[highestBuyIndex, 'Quantity']):
                # calculate the short term gains/losses
                sGain = ((df2.loc[index, 'TradePrice'])*(df2.loc[highestBuyIndex, 'Quantity']) - (
                    df2.loc[highestBuyIndex, 'TradePrice'])*(df2.loc[highestBuyIndex, 'Quantity']))
                # cumulative add the short term gains/losses
                shortTermGain = shortTermGain + sGain
                # update the quantity and buy trades in the dataframe
                quantity = quantity - (df2.loc[highestBuyIndex, 'Quantity'])
                df2.at[highestBuyIndex, 'isMatch'] = True
                df.at[highestBuyIndex, 'isMatch'] = True
            else:
                # calculate the short term gains/losses
                gain = (((df2.loc[index, 'TradePrice'])*quantity) - (
                    (df2.loc[highestBuyIndex, 'TradePrice'])*quantity))
                shortTermGain = shortTermGain + gain
                # update the dataframe
                df2.at[highestBuyIndex, 'Quantity'] = (
                    df2.loc[highestBuyIndex, 'Quantity']) - quantity
                df.at[highestBuyIndex, 'Quantity'] = (
                    df.loc[highestBuyIndex, 'Quantity']) - quantity
                df2.at[index, 'isMatch'] = True
                df.at[index, 'isMatch'] = True
                quantity = 0
            return recursiveMatchAlgo2019(df2, index, quantity, longTermGain, shortTermGain)


# define function to compute tax profile
def calculateTaxProfile(symbol):
    # get all trades for the stock
    df2 = df.loc[(df.Symbol == symbol)]
    date2019 = datetime.date(2019, 1, 1)
    totalShortTermGains2018 = 0
    totalShortTermGains2019 = 0
    totalLongTermGains2019 = 0
    # perform trade analysis only if the stock had realized gains(i.e if there is sell/btc order)
    if ('BTC' in df2.Txn.values) or ('SEL' in df2.Txn.values):
        # reverse the dataframe to start from the first trade
        df2 = df2.iloc[::-1]
        for index, row in df2.iterrows():
            # get only the sell or BTC orders
            if (row['Txn'] == 'SEL'):
                # calculate the short term gains for 2018 first
                if row['TradeDate'] < date2019:
                    # print(index)
                    quantity = row['Quantity']
                    stockShortGains = recursiveMatchAlgo2018(
                        df2, index, quantity, totalShortTermGains2018)
                    totalShortTermGains2018 = stockShortGains
                else:
                    # calculating tax profile for 2019
                    quantity = row['Quantity']
                    gains = recursiveMatchAlgo2019(
                        df2, index, quantity, totalLongTermGains2019, totalShortTermGains2019)
                    totalLongTermGains2019 = gains[1]
                    totalShortTermGains2019 = gains[0]

    return totalShortTermGains2018, totalLongTermGains2019, totalShortTermGains2019


# calculate total gains for all stocks
for stock in uniqueStockSymbol:
    #problemStocks = ['ECOL', 'WSO', 'IAA']
    problemStocks = []
    if stock not in problemStocks:
        gains = calculateTaxProfile(stock)
        shortTerm2018 = shortTerm2018 + gains[0]
        longTerm2019 = longTerm2019 + gains[1]
        shortTerm2019 = shortTerm2019 + gains[2]

print("Short term gains/losses for 2018:")
print(shortTerm2018)
print("long term gains/losses for 2019:")
print(longTerm2019)
print("Short term gains/losses for 2019:")
print(shortTerm2019)

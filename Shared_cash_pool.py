import backtrader as bt
from backtrader.indicators import *
from datetime import time
import AddPos
import DataIO
import BuyAndSell
import Log_Func
class Shared_cash_pool(bt.Strategy):
    """
    共享资金池策略类，用于管理多个投资标的的买卖决策，通过多种技术指标来决定买卖时机。
    """

    def __init__(self):
        """
        构造函数，初始化策略中使用的各种技术指标，并为每个数据源（即投资标的）设置初始值。
        """
        self.sma5 = dict()  # 存储各标的的5日简单移动平均线
        self.ema15 = dict()  # 存储各标的的15日指数加权移动平均线
        self.bolling_top = dict()  # 存储各标的的布林带上轨
        self.bolling_bot = dict()  # 存储各标的的布林带下轨
        self.notify_flag = 1  # 是否开启订单状态的通知标志
        self.out_money = dict()  # 平仓后得到的资金
        self.sell_num = dict()  # 平仓卖出的品种数量
        self.num_of_codes = dict()  # 当前持有的品种总数
        self.num_of_rest = dict()  # 每天平仓后剩余的持仓品种数
        self.sell_judge = dict()  # 判断是否卖出的标志
        self.proceeds = 0  # 总收益
        self.pending_allocation = 0  # 待分配的资金
        self.checking_time = time(14, 50)  # 检查时间点
        self.target_percent = 0.05  # 目标百分比
        self.ema12 = dict()  # 12日指数加权移动平均线
        self.ema26 = dict()  # 26日指数加权移动平均线
        self.diff = dict()  # DIF值，即短期EMA与长期EMA之差
        self.dea = dict()  # DEA值，即DIF的9日EMA
        for index, data in enumerate(self.datas):  # 遍历所有数据源
            c = data.close  # 获取收盘价
            self.sma5[data] = bt.indicators.SimpleMovingAverage(c, period=10)  # 计算5日SMA
            self.ema15[data] = bt.indicators.ExponentialMovingAverage(c, period=15)  # 计算15日EMA
            self.bolling_top[data] = bt.indicators.BollingerBands(c, period=20).top  # 计算布林带上轨
            self.bolling_bot[data] = bt.indicators.BollingerBands(c, period=20).bot  # 计算布林带下轨
            self.out_money[data] = 0  # 初始化平仓资金
            self.sell_num[data] = 0  # 初始化卖出数量
            self.num_of_codes[data] = 0  # 初始化持仓数量
            self.num_of_rest[data] = 0  # 初始化剩余持仓数量
            self.sell_judge[data] = 0  # 初始化卖出判断标志
            self.ema12[data] = bt.indicators.ExponentialMovingAverage(c, period=12)  # 计算12日EMA
            self.ema26[data] = bt.indicators.ExponentialMovingAverage(c, period=26)  # 计算26日EMA
            self.diff[data] = self.ema12[data] - self.ema26[data]  # 计算DIF
            self.dea[data] = bt.indicators.ExponentialMovingAverage(self.diff[data], period=9)  # 计算DEA

    def next(self):
        """
        在每个新的时间点上执行的策略逻辑。
        """
        if self.update_percent_judge == 0:
            DataIO.DataIO.change_target_percent(self)  # 更新目标百分比
            self.update_percent_judge += 1
        self.shared_cash()  # 调用共享现金策略方法

    def notify_order(self, order):
        """
        接收订单状态更新的通知。
        """
        if self.notify_flag:
            if order is None:
                print("Received a None Order")
                return
            if order.status in [order.Submitted, order.Accepted]:  # 订单提交或接受
                return
            if order.status in [order.Completed]:  # 订单完成
                data = order.data
                if order.isbuy():  # 买入订单
                    Log_Func.Log.log(self, f"BUY EXECUTED,{data._name}, Size:{order.executed.size}, Price:{order.executed.price:.2f}, Cost:{order.executed.value:.2f}, Commission:{order.executed.comm:.2f}")
                elif order.issell() or order.isclose():  # 卖出或平仓订单
                    Log_Func.Log.log(self, f"SELL EXECUTED,{data._name}, Size:{order.executed.size}, Price:{order.executed.price:.2f}, Cost:{order.executed.value:.2f}, Commission:{order.executed.comm:.2f}")
            elif order.status is order.Canceled:
                Log_Func.Log.log(self, 'ORDER CANCELED')
            elif order.status is order.Rejected:
                Log_Func.Log.log(self, 'ORDER REJECTED')
            elif order.status is order.Margin:
                Log_Func.Log.log(self, 'ORDER MARGIN')

    def shared_cash(self):
        """
        实现共享资金池的核心逻辑，包括买卖决策。
        """
        for data in self.datas:
            pos = self.getposition(data).size  # 获取当前持仓量
            size = self.calculate_quantity(data)  # 计算交易数量
            if pos == 0:  # 如果没有持仓
                BuyAndSell.Buy_And_Sell_Strategy.buy_function(self, line=data, size=size)  # 尝试买入
                BuyAndSell.Buy_And_Sell_Strategy.open_short_function(self, line=data, size=size)  # 尝试开空
            elif pos > 0:  # 如果持有多头
                BuyAndSell.Buy_And_Sell_Strategy.sell_function(self, line=data, size=size)  # 尝试卖出
            elif pos < 0:  # 如果持有空头
                BuyAndSell.Buy_And_Sell_Strategy.close_short_function(self, line=data)  # 尝试平空

            # 重新平衡多头和空头的仓位
            AddPos.addpos.rebalance_long_positions(self)
            AddPos.addpos.rebalance_short_positions(self)

    def calculate_quantity(self, line) -> int:
        """
        根据可用资金计算交易数量。
        """
        available_cash = self.broker.getcash() * self.target_percent  # 可用资金为总资金的5%
        close_price = line.close[0]  # 最新收盘价
        quantity = int(available_cash / close_price)  # 计算可购买的数量
        return quantity

    def stop(self):
        """
        策略结束时调用，记录最终收益。
        """
        Log_Func.Log.log(self, f'Total Proceeds from Sell Orders:{self.proceeds:.2f}')

    def print_position(self, line) -> None:
        """
        打印当前的持仓信息。
        """
        pos = self.getposition(line)  # 获取持仓信息
        print(f"品种: {line._name} 的当前仓位: {pos.size} @价格: {pos.price}")


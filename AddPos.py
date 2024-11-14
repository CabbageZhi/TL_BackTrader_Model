import backtrader as bt
import Log_Func

class addpos(bt.Strategy):
    """
    一个用于重新平衡多头和空头仓位，并在卖出后重新分配资金的策略类。
    """

    def rebalance_long_positions(self):
        """
        重新平衡多头仓位，确保每个持仓资产的比例符合目标百分比。
        """
        Log_Func.Log.log(self, f"Checking Long Position Now")  # 日志记录：检查多头仓位
        current_value = self.broker.getvalue()  # 获取当前账户总价值
        Log_Func.Log.log(self, f"Total Value:{current_value:.2f}")  # 日志记录：当前总价值

        # 获取所有持有多头仓位的资产
        held_assets = [data for data in self.datas if self.getposition(data).size > 0]

        for data in held_assets:
            position = self.getposition(data)  # 获取当前持仓
            if position.size != 0:
                current_price = data.close[0]  # 获取最新收盘价
                current_pos_value = position.size * current_price  # 计算当前持仓价值
                target_pos_value = current_value * self.target_percent  # 计算目标持仓价值
                target_pos = int(target_pos_value / current_price)  # 计算目标持仓数量

                # 日志记录：当前持仓信息
                Log_Func.Log.log(self, f"{data._name}: Long Position Now:{position.size:.2f}, Value Now:{current_pos_value:.2f}")
                Log_Func.Log.log(self, f"{data._name}: Target Long Position:{target_pos:.2f}, Target Value:{target_pos_value:.2f}")

                delta_size = target_pos - position.size  # 计算需要调整的数量

                if delta_size > 0:
                    # 如果需要增加仓位
                    Log_Func.Log.log(self, f"Rebalance Buy In:{data._name} for {delta_size:.2f}")
                    self.buy(data=data, size=delta_size)  # 执行买入操作
                elif delta_size < 0:
                    # 如果需要减少仓位
                    Log_Func.Log.log(self, f"Rebalance Sold:{data._name} for {delta_size:.2f}")
                    self.sell(data=data, size=-delta_size)  # 执行卖出操作
                elif delta_size == 0:
                    # 如果不需要调整
                    pass

    def rebalance_short_positions(self):
        """
        重新平衡空头仓位，确保每个持仓资产的比例符合目标百分比。
        """
        Log_Func.Log.log(self, f"Checking Short Position Now")  # 日志记录：检查空头仓位
        current_value = self.broker.getvalue()  # 获取当前账户总价值
        Log_Func.Log.log(self, f"Total Value:{current_value:.2f}")  # 日志记录：当前总价值

        # 获取所有持有空头仓位的资产
        held_assets = [data for data in self.datas if self.getposition(data).size < 0]

        for data in held_assets:
            position = self.getposition(data)  # 获取当前持仓
            if position.size != 0:
                current_price = data.close[0]  # 获取最新收盘价
                current_pos_value = position.size * current_price  # 计算当前持仓价值
                target_pos_value = current_value * self.target_percent * (-1)  # 计算目标持仓价值（负数）
                target_pos = int(target_pos_value / current_price)  # 计算目标持仓数量

                # 日志记录：当前持仓信息
                Log_Func.Log.log(self, f"{data._name}: Short Position Now:{position.size:.2f}, Value Now:{current_pos_value:.2f}")
                Log_Func.Log.log(self, f"{data._name}: Target Short Position:{target_pos:.2f}, Target Value:{target_pos_value:.2f}")

                delta_size = target_pos - position.size  # 计算需要调整的数量

                if delta_size > 0:
                    # 如果需要减少空头仓位
                    Log_Func.Log.log(self, f"Rebalance Close Short:{data._name} for {delta_size:.2f}")
                    self.buy(data=data, size=-delta_size)  # 执行平仓操作
                elif delta_size < 0:
                    # 如果需要增加空头仓位
                    Log_Func.Log.log(self, f"Rebalance Open Short:{data._name} for {delta_size:.2f}")
                    self.sell(data=data, size=-delta_size)  # 执行开空操作
                elif delta_size == 0:
                    # 如果不需要调整
                    pass

    def allocate_proceeds(self, proceeds, sold_data):
        """
        将卖出所得的资金重新分配到其他持仓资产中。
        """
        # 获取所有持有多头仓位且不是刚刚卖出的资产
        held_assets = [data for data in self.datas if self.getposition(data).size > 0 and data != sold_data]
        num_held = len(held_assets)  # 持仓资产的数量

        if num_held == 0:
            Log_Func.Log.log(self, "No assets held to allocate proceeds.")  # 日志记录：没有持仓资产可分配
            return

        allocation_per_asset = proceeds / num_held  # 计算每项资产应分配的资金

        Log_Func.Log.log(self, f"Allocating {allocation_per_asset:.2f} to each of {num_held} held assets.")  # 日志记录：分配资金

        for data in held_assets:
            size = int(allocation_per_asset / data.close[0])  # 计算可以购买的数量
            if size > 0:
                Log_Func.Log.log(self, f"ALLOCATE BUY, {data._name}, Size:{size}, Price:{data.close[0]:.2f}")  # 日志记录：执行买入
                self.buy(data=data, size=size)
                Log_Func.Log.log(self, "The Buying Above is Rebuy.")  # 日志记录：重新买入
            else:
                Log_Func.Log.log(self, f'Insufficient allocation for {data._name}, Allocation:{allocation_per_asset:.2f}, Price:{data.close[0]:.2f}')  # 日志记录：资金不足
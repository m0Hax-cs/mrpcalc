import math
from tabulate import tabulate

class MRP:
    def __init__(self, lead_time, safety_stock, holding_cost, setup_cost):
        self.lead_time = lead_time
        self.safety_stock = safety_stock
        self.holding_cost = holding_cost
        self.setup_cost = setup_cost

    def calculate_net_requirements(self, period_demand, on_hand_inventory):
        gross_requirements = period_demand
        net_requirements = gross_requirements + self.safety_stock - on_hand_inventory
        return max(net_requirements, 0)

    def lot_for_lot(self, net_requirements):
        return net_requirements

    def economic_order_quantity(self, average_demand):
        eoq = math.sqrt((2 * average_demand * self.setup_cost) / self.holding_cost)
        return round(eoq)

    def fixed_order_quantity(self, net_requirements, fixed_quantity):
        return max(fixed_quantity, net_requirements)

def calculate_costs(mrp, demand, starting_inventory, lead_time, technique, fixed_quantity=None):
    on_hand_inventory = starting_inventory
    total_holding_cost = 0
    total_setup_cost = 0
    scheduled_receipts = [0] * 10
    planned_orders = [0] * 10
    projected_inventory = [0] * 10
    table = []

    average_demand = sum(demand) / len(demand)
    eoq = mrp.economic_order_quantity(average_demand) if technique == "Economic Order Quantity (EOQ)" else None

    # First pass: Calculate projected inventory
    projected_inventory[0] = starting_inventory
    for period in range(10):
        if period > 0:
            projected_inventory[period] = projected_inventory[period-1]
            if period >= lead_time:
                projected_inventory[period] += planned_orders[period - lead_time]
        
        # Calculate net requirements considering safety stock
        net_requirement = max(0, demand[period] + mrp.safety_stock - projected_inventory[period])
        projected_inventory[period] -= demand[period]

        # Initialize lot_size to 0 for this period
        lot_size = 0
        setup_cost_incurred = 0

        # Check if we need to place an order
        if period + lead_time < 10:
            if technique == "Lot-for-Lot (L4L)":
                future_period = period + lead_time
                required_quantity = max(0, demand[future_period] + mrp.safety_stock - projected_inventory[period])
                
                if required_quantity > 0:
                    lot_size = required_quantity
                    planned_orders[period] = lot_size
                    setup_cost_incurred = mrp.setup_cost
                    scheduled_receipts[future_period] = lot_size
            else:
                future_periods = min(lead_time + 2, 10 - period)
                future_demand = sum(demand[period:period + future_periods])
                available_inventory = projected_inventory[period]
                
                if available_inventory - future_demand < mrp.safety_stock:
                    required_quantity = future_demand - available_inventory + mrp.safety_stock
                    
                    if technique == "Economic Order Quantity (EOQ)":
                        if available_inventory < demand[period + lead_time] + mrp.safety_stock:
                            lot_size = eoq
                            planned_orders[period] = lot_size
                            setup_cost_incurred = mrp.setup_cost
                            scheduled_receipts[period + lead_time] = lot_size
                    else:  # Fixed Order Quantity
                        lot_size = fixed_quantity
                        planned_orders[period] = lot_size
                        setup_cost_incurred = mrp.setup_cost
                        scheduled_receipts[period + lead_time] = lot_size

        period_demand = demand[period]
        on_hand_inventory = max(on_hand_inventory + scheduled_receipts[period] - period_demand, mrp.safety_stock)
        holding_cost_incurred = on_hand_inventory * mrp.holding_cost
        
        total_holding_cost += holding_cost_incurred
        total_setup_cost += setup_cost_incurred

        # Only show lot_size in table when an order is placed
        display_lot_size = lot_size if planned_orders[period] > 0 else 0

        table.append([
            period_demand,
            planned_orders[period],
            scheduled_receipts[period],
            on_hand_inventory,
            net_requirement,
            display_lot_size,
            holding_cost_incurred,
            setup_cost_incurred
        ])

    total_cost = total_holding_cost + total_setup_cost
    return total_cost, table

def transpose_table(table):
    headers = ["Attribute"] + [f"Period {i+1}" for i in range(10)]
    attributes = ["Demand", "Planned Orders", "Scheduled Receipts", "On-hand Inventory",
                  "Net Requirements", "Lot Size", "Holding Cost Incurred", "Setup Cost Incurred"]
    transposed_table = [[attributes[i]] + [row[i] for row in table] for i in range(len(attributes))]
    return headers, transposed_table

if __name__ == "__main__":
    demand = [int(input(f"Enter the demand for period {i+1}: ")) for i in range(10)]
    lead_time = int(input("Enter the lead time in periods: "))
    safety_stock = int(input("Enter the safety stock: "))
    starting_inventory = int(input("Enter the starting inventory: "))
    holding_cost = float(input("Enter the holding cost per unit per period: "))
    setup_cost = float(input("Enter the setup cost per order: "))

    mrp = MRP(lead_time, safety_stock, holding_cost, setup_cost)

    fixed_quantity = None
    if input("Do you want to specify a fixed order quantity? (y/n): ").lower() == 'y':
        fixed_quantity = int(input("Enter the fixed order quantity: "))

    techniques = ["Lot-for-Lot (L4L)", "Economic Order Quantity (EOQ)", "Fixed Order Quantity (FOQ)"]
    costs = []

    for technique in techniques:
        if technique == "Fixed Order Quantity (FOQ)" and fixed_quantity is None:
            continue
        total_cost, table = calculate_costs(mrp, demand, starting_inventory, lead_time, technique, fixed_quantity)
        costs.append((technique, total_cost, table))

    costs.sort(key=lambda x: x[1])

    print("\nResults for each technique:")
    print("-" * 80)

    for technique, total_cost, table in costs:
        headers, transposed_table = transpose_table(table)
        print(f"\nTechnique: {technique}")
        print(f"Total Cost: {total_cost}\n")
        print(tabulate(transposed_table, headers=headers, tablefmt="grid"))
        print("-" * 80)

    print("\nCost Summary:")
    for technique, total_cost, _ in costs:
        print(f"{technique}: {total_cost}")
    
    best_technique = min(costs, key=lambda x: x[1])[0]
    print(f"\nMost cost-effective technique: {best_technique}")
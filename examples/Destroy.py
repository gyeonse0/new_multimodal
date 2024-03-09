import copy
import random
from types import SimpleNamespace
import vrplib 
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import numpy.random as rnd
from typing import List

from RouteGenerator import *
from RouteInitializer import *
from FileReader import *
from Repair import *


vrp_file_path = r'C:\Users\user\Desktop\examples\data\multi_modal_data.vrp'
sol_file_path = r'C:\Users\user\Desktop\examples\data\multi_modal_data.sol'

file_reader = FileReader()
data = file_reader.read_vrp_file(vrp_file_path)
bks = file_reader.read_sol_file(sol_file_path)

globals
IDLE = 0 # 해당 노드에 드론이 트럭에 업힌 상태의 경우
FLY = 1 # 해당 노드에서 트럭이 드론의 임무를 위해 드론을 날려주는 경우
ONLY_DRONE = 2 # 해당 노드에 드론만이 임무를 수행하는 서비스 노드인 경우
CATCH = 3 # 해당 노드에서 트럭이 임무를 마친 드론을 받는 경우
ONLY_TRUCK = 4 # 해당 노드에서 트럭만이 임무를 수행하는 경우 (드론이 업혀있지 않음)
NULL = None # 해당 노드가 전체 ROUTES에 할당이 안되어 있는 경우 (SOLUTION에서 UNVISITED 한 노드)

degree_of_destruction = 0.2
customers_to_remove = int((data["dimension"] - 1) * degree_of_destruction)

class Destroy:
    def random_removal(self, state, rnd_state):
        """
        내가 설정한 파괴 상수에 따라 파괴할 고객의 수가 결정되고, 그에 따라 랜덤으로 고객노드를 제거한다.
        one_path 읽어와서 visit type update 후, 분할하면 훨씬 간단 -> 2, 4 는 1, 3 사이에 올 수 밖에 없음을 이용
        """
        destroyer = MultiModalState(state.routes, state.unassigned)
        routes = destroyer.routes
        unassigned = destroyer.unassigned
        
        repair_instance = Repair() #repair에서 넘어올때 visit_type_update 한번 더 검사
        repair_instance.truck_repair_visit_type_update(routes)
        repair_instance.drone_repair_visit_type_update(routes)
        
        self.unassigned_check(routes, unassigned)

        for customer in rnd_state.choice( #고객을 랜덤으로 선택
            range(1, data["dimension"]), customers_to_remove, replace=False):
            
            self.random_removal_visit_type_update(customer,routes,unassigned) #visit_type_update
            routes = [[point for point in route if point[1] is not None] for route in routes]

        return MultiModalState(routes, unassigned)
    
    """
    def can_drone_removal(self, state, rnd_state):
        
        #고객 데이터에서 랜딩스팟유무, 물류중량, 고객선호도의 조건만을 통과한 노드를 먼저 제거
        
        destroyer = MultiModalState(state.routes, state.unassigned)
        routes = destroyer.routes
        unassigned = destroyer.unassigned
        
        repair_instance = Repair() #repair에서 넘어올때 visit_type_update 한번 더 검사
        repair_instance.truck_repair_visit_type_update(routes)
        repair_instance.drone_repair_visit_type_update(routes)
        
        self.unassigned_check(routes, unassigned)
    
    """

    def can_drone_first_removal(self, state, rnd_state):
        destroyer = MultiModalState(state.routes, state.unassigned)
        routes = destroyer.routes
        unassigned = destroyer.unassigned

        repair_instance = Repair() #repair에서 넘어올때 visit_type_update 한번 더 검사
        repair_instance.truck_repair_visit_type_update(routes)
        repair_instance.drone_repair_visit_type_update(routes)
        
        self.unassigned_check(routes, unassigned)

        """
        고객 데이터에서 랜딩스팟유무, 물류중량, 고객선호도의 조건만을 통과한 노드를 먼저 제거
        """
        eligible_customers = [customer for customer in range(1, data["dimension"]) if data["logistic_load"][customer] < data["cargo_limit_drone"] or data["availability_landing_spot"][customer] == 1 or data["customer_drone_preference"][customer] == 1]
        finally_eligible_customers = rnd_state.choice(eligible_customers, size=min(len(eligible_customers), customers_to_remove), replace=False)
        for customer in finally_eligible_customers:
            self.random_removal_visit_type_update(customer, routes, unassigned)
            routes = [[point for point in route if point[1] is not None] for route in routes]

        return MultiModalState(routes, unassigned)


    
    
    def random_removal_visit_type_update(slef, customer, routes, unassigned):
        
        for route in routes:
                for i in range(0, len(route)-1):
                    if route[i][0] == customer:
                        if route[i][1] == IDLE:
                            route[i] = (route[i][0], NULL)
                            if (route[i][0], route[i][1]) not in unassigned:
                                unassigned.append((route[i][0], route[i][1]))

                for i in range(0, len(route)-1):
                    if route[i][0] == customer:
                        if route[i][1] == FLY:
                            route[i] = (route[i][0], NULL)
                            if (route[i][0], route[i][1]) not in unassigned:
                                unassigned.append((route[i][0], route[i][1]))
                            
                            j = i + 1
                            while j<= len(route) and (route[j][1] != FLY and route[j][1] != CATCH):
                                if route[j][1] == ONLY_DRONE:
                                    route[j] = (route[j][0], NULL)
                                    if (route[j][0], route[j][1]) not in unassigned:
                                        unassigned.append((route[j][0], route[j][1]))
                                elif route[j][1] == ONLY_TRUCK and route[j][1] != NULL:
                                    route[j] = (route[j][0], IDLE)
                                j += 1
                                
                            if route[j][1] == CATCH:  
                                route[j] = (route[j][0], IDLE)

                            if i >= 2 :
                                k = i - 1
                                while k >= 0 and route[k][1] != FLY:
                                    if route[k][1] == ONLY_DRONE:
                                        route[k] = (route[k][0], NULL)
                                        if (route[k][0], route[k][1]) not in unassigned:
                                            unassigned.append((route[k][0], route[k][1]))
                                    elif route[k][1] == ONLY_TRUCK:
                                        route[k] = (route[k][0], IDLE)
                                    k -= 1
                                
                                if k == 0 and route[k][1] == FLY:
                                    route[k] = (route[k][0], IDLE)
                                elif k > 0 and route[k][1] == FLY:
                                    if route[k - 1][1] == CATCH:
                                        route[k] = (route[k][0], IDLE)
                                    elif route[k - 1][1] == IDLE:
                                        route[k] = (route[k][0], IDLE)
                                    elif route[k - 1][1] == ONLY_DRONE:
                                        route[k] = (route[k][0], CATCH)
                                    elif route[k - 1][1] == ONLY_TRUCK:
                                        route[k] = (route[k][0], CATCH)


                for i in range(1, len(route)-1):
                    if route[i][0] == customer:
                        if route[i][1] == ONLY_DRONE:
                            route[i] = (route[i][0], NULL)
                            if (route[i][0], route[i][1]) not in unassigned:
                                unassigned.append((route[i][0], route[i][1]))
                            
                            if i == 1:
                                if route[i - 1][1] == FLY:
                                    route[i - 1] = (route[i - 1][0], IDLE)
                                
                            j = i + 1
                            while j<= len(route) and (route[j][1] != FLY and route[j][1] != CATCH):
                                if route[j][1] == ONLY_DRONE:
                                    route[j] = (route[j][0], NULL)
                                    if (route[j][0], route[j][1]) not in unassigned:
                                        unassigned.append((route[j][0], route[j][1]))
                                elif route[j][1] == ONLY_TRUCK and route[j][1] != NULL:
                                    route[j] = (route[j][0], IDLE)
                                j += 1
                                
                            if route[j][1] == CATCH:  
                                route[j] = (route[j][0], IDLE)
                            
                            
                            if i >= 2 :
                                k = i - 1
                                while k >= 0 and route[k][1] != FLY:
                                    if route[k][1] == ONLY_DRONE:
                                        route[k] = (route[k][0], NULL)
                                        if (route[k][0], route[k][1]) not in unassigned:
                                            unassigned.append((route[k][0], route[k][1]))
                                    elif route[k][1] == ONLY_TRUCK:
                                        route[k] = (route[k][0], IDLE)
                                    k -= 1
                                
                                if k == 0 and route[k][1] == FLY:
                                    route[k] = (route[k][0], IDLE)
                                elif k > 0 and route[k][1] == FLY:
                                    if route[k - 1][1] == CATCH:
                                        route[k] = (route[k][0], IDLE)
                                    elif route[k - 1][1] == IDLE:
                                        route[k] = (route[k][0], IDLE)
                                    elif route[k - 1][1] == ONLY_DRONE:
                                        route[k] = (route[k][0], CATCH)
                                    elif route[k - 1][1] == ONLY_TRUCK:
                                        route[k] = (route[k][0], CATCH)

            
                for i in range(2, len(route)-1):
                    if route[i][0] == customer:
                        if route[i][1] == CATCH:
                            route[i] = (route[i][0], NULL)
                            if (route[i][0], route[i][1]) not in unassigned:
                                unassigned.append((route[i][0], route[i][1]))
                            j = i - 1
                            while j>0 and route[j][1] != FLY:
                                if route[j][1] == ONLY_DRONE:
                                    route[j] = (route[j][0], NULL)
                                    if (route[j][0], route[j][1]) not in unassigned:
                                        unassigned.append((route[j][0], route[j][1]))
                                elif route[j][1] == ONLY_TRUCK and route[j][1] != NULL:
                                    route[j] = (route[j][0], IDLE)
                                j -= 1
                            
                            if j==0:
                                if route[j][1] == FLY:
                                    route[j] = (route[j][0], IDLE)
                                
                            elif j>=1:
                                if route[j][1] == FLY:
                                    if route[j-1][1] == CATCH and route[j-1][1] != NULL:
                                        route[j] = (route[j][0], IDLE)
                                    elif route[j-1][1] == IDLE and route[j-1][1] != NULL:
                                        route[j] = (route[j][0], IDLE)
                                    elif route[j-1][1] == ONLY_DRONE and route[j-1][1] != NULL:
                                        route[j] = (route[j][0], CATCH)
                                    elif route[j-1][1] == ONLY_TRUCK and route[j-1][1] != NULL:
                                        route[j] = (route[j][0], CATCH)
                            
                for i in range(1,len(route)-1):
                    if route[i][0] == customer:
                        if route[i][1] == ONLY_TRUCK:
                            route[i] = (route[i][0], NULL)
                            if (route[i][0], route[i][1]) not in unassigned:
                                unassigned.append((route[i][0], route[i][1]))
                                
        return routes, unassigned
    


    def unassigned_check(self, routes, unassigned):
        
        for node_id in range(1, data["dimension"]):
            is_in_routes = any(node_id == node[0] for route in routes for node in route)
            if not is_in_routes and (node_id, None) not in unassigned:
                unassigned.append((node_id, None))
                
        return unassigned
        
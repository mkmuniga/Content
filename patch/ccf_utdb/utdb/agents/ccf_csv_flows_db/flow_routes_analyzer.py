import os
import UsrIntel.R1
from tabulate import tabulate
import pandas as pd


class flow_routes_analyzer:
    def __init__(self):
        self.list_of_routes = []
        self.debug_prints = False
        
    def reset_list_of_routes(self):
        self.list_of_routes = []

    def get_bubble_df_columns(self,df):
        df = df[["Bubble", "Next Bubble"]]
        return df

    def read_csv_to_df(self, file_path):
        df = pd.read_csv(file_path, header=1, dtype=str)
        if self.debug_prints:
            print(tabulate(df, headers='keys', tablefmt='psql'))
        df = df[["Bubble", "Next Bubble"]]
        return df

    def prepare_datafram(self,df):
        df = df.apply(lambda x: x.astype(str).str.lower())
        df = df.apply(lambda x: x.astype(str).str.strip())
        return df

    def print_list_of_routes(self, list_to_print):
        for i in range(len(list_to_print)):
            print('->'.join(list_to_print[i]))

    def do_first_iteration(self, df):
        temp_df = df[df["Bubble"] == "first"]
        temp_df = temp_df.drop_duplicates(subset=None, keep='first', inplace=False)
        temp_df = temp_df.reset_index()
        if self.debug_prints:
            print(tabulate(temp_df, headers='keys', tablefmt='psql'))

        for index, row in temp_df.iterrows():
            self.list_of_routes.append([row["Bubble"], row["Next Bubble"]])

    def add_next_bubble_to_list(self, df):
        next_list_of_routes = []
        all_flows_done = True
        for i in range(len(self.list_of_routes)):
            if self.list_of_routes[i][-1] not in ["done", "first"]:
                all_flows_done = False
                temp_df = df[df["Bubble"] == self.list_of_routes[i][-1]]
                temp_df = temp_df.drop_duplicates(subset=None, keep='first', inplace=False)
                temp_df = temp_df.reset_index()
                if self.debug_prints:
                    print(tabulate(temp_df, headers='keys', tablefmt='psql'))
                for j in range(len(temp_df.index)):
                    next_list_of_routes.append(self.list_of_routes[i] +[temp_df.loc[j, ["Next Bubble"]].item()])
            else:
                next_list_of_routes.append(self.list_of_routes[i])

        self.list_of_routes = next_list_of_routes

        if not all_flows_done:
            all_flows_done = self.add_next_bubble_to_list(df)

        return all_flows_done


    def get_all_possible_flow_routes_from_csv_file(self, file_path):
        self.reset_list_of_routes()
        df = self.read_csv_to_df(file_path)
        df = self.prepare_datafram(df)
        self.do_first_iteration(df)
        self.add_next_bubble_to_list(df)
        return self.list_of_routes

    def get_all_possible_flow_routes_from_df(self, df):
        self.reset_list_of_routes()
        df = self.get_bubble_df_columns(df)
        df = self.prepare_datafram(df)
        self.do_first_iteration(df)
        self.add_next_bubble_to_list(df)
        return self.list_of_routes

def main():
    file_path = os.environ.get('WORKAREA') + "/src/val/utdb/agents/ccf_flows_csv/SnpCode_SnpData_SnpDataMig.csv"
    flow_path_analyzer_i = flow_routes_analyzer()
    list_of_routes = flow_path_analyzer_i.get_all_possible_flow_routes_from_csv_file(file_path)
    flow_path_analyzer_i.print_list_of_routes(list_of_routes)

if __name__ == "__main__":
    main()

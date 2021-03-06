from ertviz.data_loader import get_schema, get_csv_data


class PriorModel:
    def __init__(self, function, function_parameter_names, function_parameter_values):

        self.function = function
        self.function_parameter_names = function_parameter_names
        self.function_parameter_values = function_parameter_values


class ParametersModel:
    def __init__(self, **kwargs):
        self._project_id = kwargs["project_id"]
        self.group = kwargs["group"]
        self.key = kwargs["key"]
        self.priors = kwargs["prior"]
        self._schema_url = kwargs["schema_url"]
        self._realizations = kwargs.get("realizations")
        self._data_df = None

    def data_df(self):
        if self._data_df is None:
            realizations_schema = get_schema(self._schema_url)
            self._data_df = get_csv_data(
                realizations_schema["alldata_url"], project_id=self._project_id
            ).T
            self._data_df.columns = [
                schema["name"]
                for schema in realizations_schema["parameter_realizations"]
            ]
            self._data_df.index.name = self.key
        return self._data_df

import dash
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
from ertviz.models import EnsembleModel, MultiHistogramPlotModel


def _prev_value(current_value, options):
    try:
        index = options.index(current_value)
    except ValueError:
        index = None
    if index > 0:
        return options[index - 1]
    return current_value


def next_value(current_value, options):
    try:
        index = options.index(current_value)
    except ValueError:
        index = None
    if index < len(options) - 1:
        return options[index + 1]
    return current_value


def multi_parameter_controller(parent, app):
    @app.callback(
        Output(parent.uuid("parameter-selector"), "options"),
        [
            Input(parent.uuid("ensemble-selection-store"), "data"),
        ],
    )
    def update_parameter_options(selected_ensembles):
        if not selected_ensembles:
            raise PreventUpdate
        ensemble_id, _ = selected_ensembles.popitem()
        ensemble = parent.ensembles.get(
            ensemble_id,
            EnsembleModel(ref_url=ensemble_id, project_id=parent.project_identifier),
        )
        parent.ensembles[ensemble_id] = ensemble
        parent.parameter_models[ensemble_id] = ensemble.parameters
        options = [
            {"label": parameter_key, "value": parameter_key}
            for parameter_key in parent.parameter_models[ensemble_id]
        ]
        return options

    @app.callback(
        Output(
            {"id": parent.uuid("parameter-scatter"), "type": parent.uuid("graph")},
            "figure",
        ),
        [
            Input(parent.uuid("parameter-selector"), "value"),
            Input(parent.uuid("hist-check"), "value"),
        ],
        [State(parent.uuid("ensemble-selection-store"), "data")],
    )
    def _update_histogram(parameter, hist_check_values, selected_ensembles):
        if not selected_ensembles:
            raise PreventUpdate
        data = {}
        colors = {}
        priors = {}
        for ensemble_id, color in selected_ensembles.items():
            if parameter in parent.parameter_models[ensemble_id]:
                parameter_model = parent.parameter_models[
                    ensemble_id
                ][parameter]
                data[parent.ensembles[ensemble_id]._name] = parameter_model.data_df()
                colors[parent.ensembles[ensemble_id]._name] = color["color"]

                if parameter_model.priors:
                    priors[parent.ensembles[ensemble_id]._name] = parameter_model.priors
                    print( parameter_model.priors.function)
                    print( parameter_model.priors.function_parameter_names)
                    print( parameter_model.priors.function_parameter_values)

        parent.parameter_plot = MultiHistogramPlotModel(
            data,
            colors=colors,
            hist="hist" in hist_check_values,
            kde="kde" in hist_check_values,
            priors=priors
        )

        return parent.parameter_plot.repr

    @app.callback(
        Output(parent.uuid("parameter-selector"), "value"),
        [
            Input(parent.uuid("prev-btn"), "n_clicks"),
            Input(parent.uuid("next-btn"), "n_clicks"),
            Input(parent.uuid("parameter-selector"), "options"),
        ],
        [
            State(parent.uuid("parameter-selector"), "value"),
        ],
    )
    def _set_parameter_from_btn(_prev_click, _next_click, parameter_options, parameter):

        ctx = dash.callback_context.triggered

        callback = ctx[0]["prop_id"]
        if callback == f"{parent.uuid('prev-btn')}.n_clicks":
            parameter = _prev_value(
                parameter, [option["value"] for option in parameter_options]
            )
        elif callback == f"{parent.uuid('next-btn')}.n_clicks":
            parameter = next_value(
                parameter, [option["value"] for option in parameter_options]
            )
        elif parameter_options:
            parameter = parameter_options[0]["value"]
        else:
            raise PreventUpdate
        return parameter

    @app.callback(
        Output(parent.uuid("hist-check"), "options"),
        [
            Input(parent.uuid("parameter-selector"), "value"),
        ],
        [
            State(parent.uuid("hist-check"), "options"),
            State(parent.uuid("ensemble-selection-store"), "data")
        ],
        
    )
    def _set_parameter_from_btn(parameter, plotting_options, selected_ensembles):
        has_priors = False
        for ensemble_id, color in selected_ensembles.items():
            if parameter in parent.parameter_models[ensemble_id]:
                parameter_model = parent.parameter_models[
                    ensemble_id
                ][parameter]
                if parameter_model.priors:
                    has_priors = True
                    break
        prior_option = {"label": "prior", "value": "prior"}
        if has_priors and prior_option not in plotting_options:
            plotting_options.append(prior_option)
        if not has_priors and prior_option in plotting_options:
            plotting_options.remove(prior_option)
        return plotting_options
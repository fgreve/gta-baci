from shiny import App, render, ui, reactive, req
from shinywidgets import output_widget, render_widget
from shared import gta_df, product_description_dict, affected_products, country_code_df, get_baci_exporter_df
import pandas as pd
import plotly.express as px
from pathlib import Path
import shinyswatch

app_ui = ui.page_fluid(
    ui.panel_title(ui.h2("Dashboard: Global Trade Alert GTA & International Trade Database at the Product-Level BACI")),

    ui.layout_columns(  
        ui.input_date_range("daterange", "Date range", start="2020-01-01"),  
        # ui.output_text("date_range_value"),

        ui.input_selectize("implementing", 
                           "Implementing Jurisdiction:", 
                           sorted(list(gta_df['Implementing Jurisdiction'].unique())),
                           selected='United States of America',
                           ),  
        # ui.output_text("implementing_value"),

        ui.input_selectize("affected", 
                           "Affected Jurisdiction:", 
                           sorted(list(gta_df['Affected Jurisdiction'].unique())),
                           selected='Chile',
                           ),  
        # ui.output_text("affected_value"),
    ),
    ui.layout_columns(  
        ui.card(  
            ui.card_header("GTA Table: Global Trade Alert"),
            ui.p(""),
            ui.output_data_frame("gta_filter_df"),  
        ),   
    ),  

    ui.layout_columns(  
        ui.card(  
            ui.card_header("Product Detail"),
            ui.p("BACI: International Trade Database at the Product-Level."),
            ui.output_data_frame("products_values"),  
        ), 
        ui.card(  
            ui.card_header("Historical Trade"),
            ui.p("BACI: International Trade Database at the Product-Level."),
            ui.output_data_frame("product_table"),  
        ),         
    ), 

    ui.layout_columns(  
        ui.card(  
            ui.card_header("Trade Value"),
            ui.p("BACI: International Trade Database at the Product-Level."),
            output_widget("plot_value"),  
        ), 
        ui.card(  
            ui.card_header("Trade Quantity"),
            ui.p("BACI: International Trade Database at the Product-Level."),
            output_widget("plot_quantity"),  
        ),         
    ),
    # theme=shinyswatch.theme.spacelab,
)


def server(input, output, session):
    @render.text
    def date_range_value():
        return f"{input.daterange()[0]} to {input.daterange()[1]}"


    @render.text
    def implementing_value():
        return f"{input.implementing()}" 


    @render.text
    def affected_value():
        return f"{input.affected()}" 


    @render.data_frame
    def gta_filter_df():
        df_filter = gta_df[gta_df['Implementing Jurisdiction']==input.implementing()]
        df_filter = df_filter[df_filter['Affected Jurisdiction']==input.affected()]
        df_filter = df_filter[df_filter['Announcement Date']>=input.daterange()[0]]
        df_filter = df_filter[df_filter['Announcement Date']<=input.daterange()[1]]
        return render.DataGrid(df_filter, filters=True, selection_mode="rows") 
    

    @render.data_frame
    def products_values():
        data_selected = gta_filter_df.data_view(selected=True)
        req(not data_selected.empty)
        key = list(data_selected.index)[0]

        AffectedProducts = affected_products(key)
        products = AffectedProducts[str(key)]
        
        dictio = {}
        for p in products:
            dictio[p] = product_description_dict[p]

        df = pd.DataFrame()
        df['Product'] = list(dictio.keys())
        df['Description'] = list(dictio.values())
        return render.DataGrid(df, filters=True, selection_mode="rows")


    @reactive.calc
    def filtered_df():
        data_selected = products_values.data_view(selected=True)
        req(not data_selected.empty)
        
        product = data_selected['Product'].values[0]

        implementing_code = country_code_df[country_code_df['country']==input.implementing()]['country_code'].values[0]
        affected_code = country_code_df[country_code_df['country']==input.affected()]['country_code'].values[0]

        baci_exporter_df = get_baci_exporter_df(affected_code)
        baci_exporter_df = baci_exporter_df[baci_exporter_df['importer']==implementing_code]
        baci_exporter_df = baci_exporter_df[baci_exporter_df['product']==product]
        return baci_exporter_df
    

    @render.data_frame
    def product_table():
        return render.DataGrid(filtered_df(), filters=False, selection_mode="rows")


    @render_widget
    def plot_value():
        return px.line(
            filtered_df(),
            x="year",
            y="value",
            title="Value",
        )


    @render_widget
    def plot_quantity():
        return px.line(
            filtered_df(),
            x="year",
            y="quantity",
            title="Quantity",
        )


app = App(app_ui, server, debug=True)



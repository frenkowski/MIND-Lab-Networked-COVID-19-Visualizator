from dash.dependencies import Input, Output, State, ALL
import dash, glob, base64, pickle, dash_table, os
import dash_bootstrap_components as dbc
from pathlib import Path
import plotly.graph_objs as go
import glob, os, pickle
from collections import Counter
import dash_gif_component as gif
import dash_html_components as html

from src.app import app
#import for grid layout
import src.net_layout as net_layout

# read and check available dumps in network_dumps folder
def read_available_dumps():
    files = os.listdir('network_dumps/')
    all_pickles_names = [i for i in files if i.endswith('.pickle')]
    first_dump = True
    current_nets = ""
    networks_dictionary = {}
    error_read = []
    for file in all_pickles_names:
        current_file_path = Path("network_dumps/{}".format(file))
        
        with open(current_file_path, "rb") as f:
            try:
                dump = pickle.load(f)
                nets = dump['nets']
                name = file.split(".")[0]

                # check GIF
                test_sim_png = Path('assets/{}_simulation.png'.format(name))
                test_sim_gif = Path('assets/{}_simulation.gif'.format(name))

                #check
                test_image = Path('images/{}_sim0.jpeg'.format(name))

                if test_sim_png.exists() and test_sim_gif .exists() and test_image.exists():
                    networks_dictionary[name] = name
                    if first_dump:
                        current_nets = name
                        first_dump = False
                else:
                    
                    error_read.append(file)
                    continue
                    
            except:
                error_read.append(file)
                continue
    
    print("networks_dictionary: ", networks_dictionary)      
    # net to load at first launch
    return networks_dictionary, current_nets, error_read




@app.callback([Output("network_id", "options"), Output("network_id", "value"), Output("read_alert", "children"), Output("noFiles", "children")], [Input("refresh", "n_clicks")])
def refresh_button_click(n_clicks):
    print("refresh_button_click")
    networks_dictionary, current_nets, errors = read_available_dumps()

    if len(errors) > 0:
        read_alert = dbc.Alert("Can't read this files: " + str(errors) + "\n use only full dump type for this tab" ,  color="danger",  duration=6000)
    else:
        read_alert = dbc.Alert("Succesfully read all files" , id = 'alert_id', color="success",  duration=6000)
            
    # no file available
    if current_nets != "":

        '''fp_in = Path("network_dumps/{}.pickle".format(networks_dictionary[current_nets]))
        nets = list()
        with open(fp_in, "rb") as f:
            dump = pickle.load(f)
            nets = dump['nets']


        history_path = "assets/network_history_{}.pickle".format(networks_dictionary[current_nets])

        with open(history_path, "rb") as f:
            current_network_history = pickle.load(f)
        '''
        # fix position of nodes for plotting
        #layout = nets[0].layout("large")
        #grid = net_layout.Get_Grid_Div(app, "cyto_1", net_layout.create_network_data(nets[0]))
        bigErrorAlert = []

    else:
        bigErrorAlert = dbc.Alert("No simulation accessible, put the full dumps in the \"network_dumps\" folder and use the create_images module then run this app",  color="danger")

    new_options = [{"label": col, "value": col} for col in networks_dictionary.keys()]
    return [new_options, current_nets, read_alert, bigErrorAlert]


@app.callback([Output("day_sim", "max"), Output("day_sim", "marks"),  Output("slider_day_sim_trend", "max") , Output("slider_day_sim_trend", "marks"), Output("slider_day_sim_trend", "value")], [Input("network_id", "value")])
def update_slider_marks_and_max(network_id):
    print("update_slider_marks_and_max: ", network_id)
    # no file available
    if network_id is not None:

        history_path = "assets/network_history_{}.pickle".format(network_id)

        with open(history_path, "rb") as f:
            current_network_history = pickle.load(f)

        tot = len(current_network_history) - 1
        
        marks = {
                0: {'label': '0'},
                tot: {'label': str(tot)}
        }

        #value = 0

    else:
        tot = 0
        grid = []
        marks = {}
        #value = 0

    return [tot, marks, tot, marks, tot]

@app.callback([Output("gif_id","children"), Output("gif_id_inf","children"), Output("stats", "children")], [Input("network_id", "value")])
def update_current_nets(network_id):
    print("update_current_nets: ", network_id)
    if network_id is not None:
        current_nets = network_id
        
        new_path = Path("network_dumps/{}.pickle".format(network_id))
        nets = list()
        with open(new_path, "rb") as f:
            dump = pickle.load(f)
            nets = dump['nets']
        

        history_path = "assets/network_history_{}.pickle".format(network_id)

        with open(history_path, "rb") as f:
            current_network_history = pickle.load(f)

        tot = len(current_network_history) - 1

        # fixed position of node
        layout = nets[0].layout("large")
        clickBack = 0
        clickForward = 0

        # GIF load
        sim_png = Path('assets/{}_simulation.png'.format(network_id))
        sim_gif = Path('assets/{}_simulation.gif'.format(network_id))

        encoded_sim_png = base64.b64encode(open(sim_png, 'rb').read())
        encoded_sim_gif = base64.b64encode(open(sim_gif, 'rb').read())


        GIF = gif.GifPlayer(
                gif= 'data:image/gif;base64,{}'.format(encoded_sim_gif.decode()),
                still= 'data:image/png;base64,{}'.format(encoded_sim_png.decode()),
                autoplay = True,
              )

        sim_png = Path('assets/{}_inf_simulation.png'.format(network_id))
        sim_gif = Path('assets/{}_inf_simulation.gif'.format(network_id))

        encoded_sim_png = base64.b64encode(open(sim_png, 'rb').read())
        encoded_sim_gif = base64.b64encode(open(sim_gif, 'rb').read())
        
        GIF_inf = gif.GifPlayer(
                gif= 'data:image/gif;base64,{}'.format(encoded_sim_gif.decode()),
                still= 'data:image/png;base64,{}'.format(encoded_sim_png.decode()),
                autoplay = True,
              )
        
        # stats div
        tot_infected = 0
        number_of_nodes = len(nets[0].vs)
        tot_infected = number_of_nodes - current_network_history[tot]['S']

        contacts_sum = 0
        for day in range(len(current_network_history)):
            degree = nets[day].degree()
            contacts_sum += sum(degree) / 2   #edge are undirected then necessary /2
        
        avg_contacts = int( contacts_sum / (number_of_nodes * tot))


        stats_current_net =  html.Div(children = [
                        html.H3("Simulation summary"),
                        html.P('Number of nodes: ' + str(number_of_nodes)),
                        html.P('Average dayly number of contacts: ' + str(avg_contacts)),
                        html.P('Simulation duration: ' + str(tot)),
                        html.P('Total infected people: ' + str(tot_infected)),
                        html.P('Total dead people: ' + str(current_network_history[tot]['D']))
                        ])
        

        return [GIF, GIF_inf, stats_current_net]
    else:
        return [[], [], []]

@app.callback([Output("graph_sim", "figure"), 
               Output("div_spin", "children"), 
               Output("img_day1", "figure"), 
               Output("img_day2", "figure"), 
               Output("graphImg1", "figure"), 
               Output("graphImg2", "figure"),
               Output('cyto-container', 'children')
               ], 
              [Input("day_sim", "value")], [State("network_id", "value")])
def update_graphics(day, network_id):
    """
    Update the slderbar when button forward or back is clicked
    
    Parameters
    ----------
    
    day: integer
        Current day of simulation

    

    Return
    ------
    outputs: list of all graphics and images to update
        graph_sim plotly interactive figure 
        div_spin use to show spinner loading component
        img_day1 plotly figure to show prev graph situation in a image
        img_day2 plotly figure to show current situation in a image
        graphImg1 plotly figure that show summary of the status of the prev network
        graphImg2 plotly figure that show summary of the status of the current network
        cyto-container Div to plot grid-layout
    """
    #print("day_net_layout", day_net_layout)

    #day_net_layout = day_net_layout if day_net_layout != "" or day_net_layout is not None else "grid"

    #global layout, tot, current_nets, 
    print("update_graphics: " + str(network_id) + " day " + str(day))

    if network_id is not None:
        # read network to plot
       
        new_path = Path("network_dumps/{}.pickle".format(network_id))
        loc_nets = list()
        with open(new_path, "rb") as f:
            loc_dump = pickle.load(f)
            loc_nets = loc_dump['nets']
            

        loc_history_path = "assets/network_history_{}.pickle".format(network_id)

        with open(loc_history_path, "rb") as f:
            loc_current_network_history = pickle.load(f)

        loc_tot = len(loc_current_network_history) - 1

            # fixed position of node
        loc_layout = loc_nets[0].layout("large")

        
        G = loc_nets[day]

        # plotly graph 
        colors = {'S':'#0000ff', 'E':'#ffa300', 'I':'#ff0000', 'D':'#000000', 'R':'#00ff00'}
        vertex_color = [colors[status] for status in G.vs["agent_status"]]
        
        node_text = []
        node_trace_x = []
        node_trace_y = []

        infected = [vertex.index for vertex in G.vs if vertex["agent_status"] == 'I']

        #add a pos attribute to each node
        for node in G.vs:
            node_text.append('State: ' + str(node['agent_status']))
            x, y = loc_layout[node.index]
            node_trace_x += tuple([x])
            node_trace_y += tuple([y])

        edge_trace_x = []
        edge_trace_y = []
        edge_trace_x_red = []
        edge_trace_y_red = []


        for edge in G.es:
            x0, y0 = loc_layout[edge.source]
            x1, y1 = loc_layout[edge.target]

            if edge.source in infected or edge.target in infected:
                edge_trace_x_red += tuple([x0, x1, None])
                edge_trace_y_red += tuple([y0, y1, None])
            else:
                edge_trace_x += tuple([x0, x1, None])
                edge_trace_y += tuple([y0, y1, None])
                


        edge_trace_gray = go.Scatter(
            x=edge_trace_x,
            y=edge_trace_y,
            line=dict(width=0.3,color='#888'),
            hoverinfo='none',
            mode='lines')

        edge_trace_red = go.Scatter(
            x=edge_trace_x_red,
            y=edge_trace_y_red,
            line=dict(width=0.7,color='#ff0000'),
            hoverinfo='none',
            mode='lines')


        node_trace = go.Scatter(
            x= node_trace_x,
            y= node_trace_y,
            text= node_text,
            mode='markers',
            hoverinfo='text',
            marker=dict(
                #showscale=True,
                # colorscale options
                #'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
                #'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
                #'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
                #colorscale='YlGnBu',
                #reversescale=True,
                color= vertex_color,
                size=20,
                #colorbar=dict(
                #    thickness=15,
                #    title='Node Connections',
                #    xanchor='left',
                #    titleside='right'
                #),  
                line=dict(width=2)))


        fig = go.Figure(data=[edge_trace_gray, edge_trace_red, node_trace],
                     layout=go.Layout(
                        title='<br>Network Graph day '+ str(day),
                        titlefont=dict(size=16),
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        annotations=[ dict(
                            text="",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002 ) ],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
        config = {'displaylogo': False}

        #fig.show(config=config)
        
        # get current and prev images
        if day > 0:
            image_filename1 = Path('images/{}_sim'.format(network_id) + str(day -1)  + '.jpeg')
            image_filename2 = Path('images/{}_sim'.format(network_id) + str(day)  + '.jpeg')
            day_prev = day -1
        else:
            image_filename1 = Path('images/{}_sim0.jpeg'.format(network_id))
            image_filename2 = Path('images/{}_sim0.jpeg'.format(network_id))
            day_prev = 0


        encoded_image1 = base64.b64encode(open(image_filename1, 'rb').read())
        encoded_image2 = base64.b64encode(open(image_filename2, 'rb').read())
        

        # create graph for display images 
        src_image1 = go.Figure()

        # Constants
        img_width = 500
        img_height = 500
        scale_factor = 0.7

        # Add invisible scatter trace.
        # This trace is added to help the autoresize logic work.
        src_image1.add_trace(
            go.Scatter(
                x=[0, img_width * scale_factor],
                y=[0, img_height * scale_factor],
                mode="markers",
                marker_opacity=0
            )
        )

        # Configure axes
        src_image1.update_xaxes(
            visible=False,
            range=[0, img_width * scale_factor]
        )

        src_image1.update_yaxes(
            visible=False,
            range=[0, img_height * scale_factor],
            # the scaleanchor attribute ensures that the aspect ratio stays constant
            scaleanchor="x"
        )

        # Add image
        src_image1.add_layout_image(
            dict(
                x=0,
                sizex=img_width * scale_factor,
                y=img_height * scale_factor,
                sizey=img_height * scale_factor,
                xref="x",
                yref="y",
                opacity=1.0,
                layer="below",
                sizing="stretch",
                source='data:image/png;base64,{}'.format(encoded_image1.decode()))
        )

        # Configure other layout
        src_image1.layout.update(
            width=img_width * scale_factor,
            height=img_height * scale_factor,
            margin={"l": 0, "r": 0, "t": 0, "b": 0},
        )


        src_image2 = go.Figure()

        # Constants

        # Add invisible scatter trace.
        # This trace is added to help the autoresize logic work.
        src_image2.add_trace(
            go.Scatter(
                x=[0, img_width * scale_factor],
                y=[0, img_height * scale_factor],
                mode="markers",
                marker_opacity=0
            )
        )

        # Configure axes
        src_image2.update_xaxes(
            visible=False,
            range=[0, img_width * scale_factor]
        )

        src_image2.update_yaxes(
            visible=False,
            range=[0, img_height * scale_factor],
            # the scaleanchor attribute ensures that the aspect ratio stays constant
            scaleanchor="x"
        )

        # Add image
        src_image2.add_layout_image(
            dict(
                x=0,
                sizex=img_width * scale_factor,
                y=img_height * scale_factor,
                sizey=img_height * scale_factor,
                xref="x",
                yref="y",
                opacity=1.0,
                layer="below",
                sizing="stretch",
                source='data:image/png;base64,{}'.format(encoded_image2.decode()))
        )

        # Configure other layout
        src_image2.update_layout(
            width=img_width * scale_factor,
            height=img_height * scale_factor,
            margin={"l": 0, "r": 0, "t": 0, "b": 0},
        )


        
        # graph current summary situation 

        s = loc_current_network_history[day]["S"]
        e = loc_current_network_history[day]["E"]
        i = loc_current_network_history[day]["I"]
        r = loc_current_network_history[day]["R"]
        d = loc_current_network_history[day]["D"]


        current = {
                'data': [
                    {'x': [1], 'y': [s], 'type': 'bar', 'name': 'S', 'marker' : {'color': colors['S']}},
                    {'x': [1], 'y': [e], 'type': 'bar', 'name': 'E', 'marker' : {'color': colors['E']}},
                    {'x': [1], 'y': [i], 'type': 'bar', 'name': 'I', 'marker' : {'color': colors['I']}},
                    {'x': [1], 'y': [r], 'type': 'bar', 'name': 'R', 'marker' : {'color': colors['R']}},
                    {'x': [1], 'y': [d], 'type': 'bar', 'name': 'D','marker' : {'color': colors['D']}},
                ],
                'layout': {
                    'title': 'Population summary at Day ' + str(day)
                }
        }

        
        # graph prev summary situation 
        s = loc_current_network_history[day_prev]["S"]
        e = loc_current_network_history[day_prev]["E"]
        i = loc_current_network_history[day_prev]["I"]
        r = loc_current_network_history[day_prev]["R"]
        d = loc_current_network_history[day_prev]["D"]

        prev = {
                'data': [
                    {'x': [1], 'y': [s], 'type': 'bar', 'name': 'S', 'marker' : {'color': colors['S']}},
                    {'x': [1], 'y': [e], 'type': 'bar', 'name': 'E', 'marker' : {'color': colors['E']}},
                    {'x': [1], 'y': [i], 'type': 'bar', 'name': 'I', 'marker' : {'color': colors['I']}},
                    {'x': [1], 'y': [r], 'type': 'bar', 'name': 'R', 'marker' : {'color': colors['R']}},
                    {'x': [1], 'y': [d], 'type': 'bar', 'name': 'D','marker' : {'color': colors['D']}},
                ],
                'layout': {
                    'title': 'Population summary at Day ' + str(day_prev)
                }
        }

        save_pdf = False
        if save_pdf == True:
            fig.write_image("graph.pdf")
            prevFig = go.Figure(prev)
            prevFig.write_image("prev.pdf")
            currentFig = go.Figure(current)
            currentFig.write_image("current.pdf")


        return [fig, [], src_image1, src_image2, prev, current, net_layout.Get_Grid_Div(app, "cyto_" + str(day) + "_" + network_id.strip(), net_layout.create_network_data(G))] 
    
    else:
        return [{}, [], {}, {}, {}, {}, []] 

#show the simulaton until the current simualtion day
@app.callback([Output("graph_evolution_sim", "figure"), Output("simulation_image_trend","figure")], [Input("slider_day_sim_trend", "value")], [State("network_id", "value")])
def update_plot_simulation_trend(day, network_id):
    print("update_plot_simulation_trend: " + str(network_id) + " day " + str(day))

    """
    Update the simulation graph according to slider value 
    
    Parameters
    ----------
    
    day: integer
        Current day of simulation

    new_max: integer
        Current max number of day in simulation

    Return
    ------
    outputs: simulation_image_trend (figure)
        plotly figure that show the simulaton until the current simualtion day
    """

    if network_id is not None:
        x_axis = []
        y_S = []
        y_E = []
        y_I = []
        y_R = []
        y_D = []

        history_path = "assets/network_history_{}.pickle".format(network_id)

        with open(history_path, "rb") as f:
            current_network_history = pickle.load(f) 

        for i in range(day):
            x_axis.append(i)
            y_S.append(current_network_history[i]["S"])
            y_E.append(current_network_history[i]["E"])
            y_I.append(current_network_history[i]["I"])
            y_R.append(current_network_history[i]["R"])
            y_D.append(current_network_history[i]["D"])

        graph = {'data': [
                        {'x': x_axis, 'y': y_S, 'type': 'line', 'name': 'S', 'marker' : {'color': '#0000ff'}},
                        {'x': x_axis, 'y': y_E, 'type': 'line', 'name': 'E', 'marker' : {'color': '#ffa300'}},
                        {'x': x_axis, 'y': y_I, 'type': 'line', 'name': 'I', 'marker' : {'color': '#ff0000'}},
                        {'x': x_axis, 'y': y_R, 'type': 'line', 'name': 'R', 'marker' : {'color': '#00ff00'}},
                        {'x': x_axis, 'y': y_D, 'type': 'line', 'name': 'D','marker' : {'color': '#000000'}},
                    ],
                    'layout': {
                        'title': 'Lineplot associated with the network of the day ' + str(day) 
                    }
                }


        RANGE = [0, 1]
       
        image_filename = Path('images/{}_sim'.format(network_id) + str(day)  + '.jpeg')

        
        encoded_image = base64.b64encode(open(image_filename, 'rb').read())

        img = {'data':[], 
        'layout': {
                    'xaxis': {
                        'range': RANGE,
                        'showgrid':False,
                        'zeroline': False,
                        'showline': False,
                        'ticks': '',
                        'showticklabels': False,
                    },
                    'yaxis': {
                        'range': RANGE,
                        'scaleanchor': 'x',
                        'scaleratio': 1,
                        'zeroline': False,
                        'showgrid':False,
                       'showline': False,
                                           'ticks': '',
                        'showticklabels': False,
                    },
                    'height': 500,
                    'images': [{
                        'xref': 'x',
                        'yref': 'y',
                        'x': RANGE[0],
                        'y': RANGE[1],
                        'sizex': RANGE[1] - RANGE[0],
                        'sizey': RANGE[1] - RANGE[0],
                        'sizing': 'stretch',
                        'layer': 'below',
                        'source': 'data:image/png;base64,{}'.format(encoded_image.decode())
                    }],
                    
                    
                    }
        }
        

        return [graph, img]
    else:
        return [{}, {}]


@app.callback(
    [Output('back', 'disabled'), Output('forward', 'disabled')],
    [Input("day_sim", "value")], [State("network_id", "value")],
)

# check enable button forward and back
def enable__disable_buttons(sim_day, network_id):
    print("check ", sim_day)

    """
    Enable or diseable forward and back buttons in according to the current value of the slider.
    
    Parameters
    ----------
    
    sim_day: integer
        Current day of simulation

    Return
    ------
    disabled: list [bool, bool]
        [backDisabled, ForwardDisabled] if True the specif button is disable if True is clickable 

    """
    
    if network_id is not None:
        
        loc_history_path = "assets/network_history_{}.pickle".format(network_id)

        with open(loc_history_path, "rb") as f:
            loc_current_network_history = pickle.load(f)

        loc_tot = len(loc_current_network_history) - 1

        if sim_day == 0:
            return [True, False]
        elif sim_day >= loc_tot:
            return [False, True]
        else:
            return [False, False]
    else:
        return [False, False]

@app.callback([Output("day_sim", "value"), Output("div_back", "value"), Output("div_forward", "value")], [Input("back", "n_clicks"), Input("forward", "n_clicks"), Input("network_id", "value")], [State("day_sim", "value"), State("div_back", "value"), State("div_forward", "value")])#, State("network_id", "value")])
def update_slider_value(currentClickBack, currentClickForward, network_id, day_sim, value_back, value_forward):
    """
    Update the slderbar when button forward or back is clicked
    
    Parameters
    ----------
    
    currentClickBack: integer
        Number of click of the back button, use to avoid updating first auto-call e refresh in dash

    currentClickForward: integer
        Number of click of the forward button, use to avoid updating first auto-call e refresh in dash
    
    day_sim: integer
        Current day of simulation

    Return
    ------
    disabled: list [bool, bool]
        [backDisabled, ForwardDisabled] if True the specif button is disable if True is clickable 

    """
    print("update_slider_value " + " back: " + str(currentClickBack) + " forward: " + str(currentClickForward) + " net_id: " + str(network_id) +  " day_sim " + str(day_sim))
    if network_id is not None:
        if currentClickBack is not None and currentClickBack > value_back:
            return [day_sim - 1, value_back + 1, value_forward]
        elif currentClickForward is not None and currentClickForward > value_forward:
            return [day_sim + 1, value_back, value_forward + 1]
        else:
            return [0, 0, 0]
    else:
        return [0, 0, 0]




# callback tab 2
def compute_network_history_from_full_dump(full_dump):
    """
    Compute the dayly counter of Susceptibile, Exposed, Infectedm, Recovered, Dead, Quarantine, Tested, Positive.
    Return dictionary with keys S, E, I, R, D, Q, tot, tested, positive and values list of dayly counter according to
    the keys.
    
    Parameters
    ----------
    nets: list of ig.Graph()
        List of dayly igraph objects

    Return
    ------
    network_history: dictionary of agent status and tests
        Dictionary keys:    S, E, I, R, D, Q, tot, tested, positive 
                   values:  list of dayly counter of key
    """
    nets = full_dump['nets']
    network_history = {}
    network_history['S'] = list()
    network_history['E'] = list()
    network_history['I'] = list()
    network_history['R'] = list()
    network_history['D'] = list()
    network_history['quarantined'] = list()
    network_history['positive'] = list()
    network_history['tested'] = list()
    network_history['total'] = list()

    for day in range(len(nets)):
        G = nets[day]

        network_report = Counter(G.vs["agent_status"])

        tested = 0
        quarantined = 0
        positive = 0
        
        for node in G.vs:
            if node["test_result"] != -1:
                tested += 1
            if node["test_result"] == 1:
                positive += 1
            if node["quarantine"] != 0:
                quarantined += 1

        tot = sum(network_report.values())
        network_report['quarantined'] = quarantined
        network_report['positive'] = positive
        network_report['tested'] = tested


        network_history['S'].append(network_report['S'])
        network_history['E'].append(network_report['E'])
        network_history['I'].append(network_report['I'])
        network_history['R'].append(network_report['R'])
        network_history['D'].append(network_report['D'])
        network_history['quarantined'].append(network_report['Q'])
        network_history['positive'].append(network_report['positive'])
        network_history['tested'].append(network_report['tested'])
        network_history['total'].append(tot)
        network_history['parameters'] = full_dump['parameters']

    return network_history

# read only pickle file
def parse_contents(name, content):

    content_type, content_string = content.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        # read pickle

        file_content = pickle.loads(decoded)
        #print("Parameters", file_content['parameters'])
        if isinstance(file_content, dict):
            for key in file_content.keys():
                if not isinstance(file_content[key] , (list, dict)):
                    return "Error"
            return file_content
        else:
            return "Error"
        
    except Exception as e:
        print(e)
        return "Error"


def normalize_data_to_plot(dict_upload_files):
    norm_dict_upload_files ={}

    for file in dict_upload_files.keys():
        # full dump
        if len(dict_upload_files[file].keys()) == 2:
            norm_dict_upload_files[file] = compute_network_history_from_full_dump(dict_upload_files[file])

        
        # light dump
        elif isinstance(dict_upload_files[file], dict):
            norm_dict_upload_files[file] = dict_upload_files[file]
            #print(dict_upload_files[file])

    return norm_dict_upload_files


def create_all_graphs(dict_upload_files, save_pdf = True):

        # normalize light e full dumps
        norm_dict_upload_files = normalize_data_to_plot(dict_upload_files)


        # comparison simulation results
        graph_infected = dict({'data': [],
                'layout': {'title': 'Comparison infected',
                           'xaxis':{'title':'Day'},
                           'yaxis':{'title':'Number of infected'}
                          }
               })

        for filename in norm_dict_upload_files.keys():
            infected = [norm_dict_upload_files[filename]['I'][i] + norm_dict_upload_files[filename]['E'][i] for i in range(len(norm_dict_upload_files[filename]['I']))]
            graph_infected['data'].append({"type": "scatter", 'x': list(range(len(infected))), "y":  infected, 'name': filename.split('.')[0]})
        

        # comparison dead all simulation
        graph_dead = dict({'data': [],
                'layout': {'title': 'Comparison dead',
                           'xaxis':{'title':'Day'},
                           'yaxis':{'title':'Number of dead'}
                          }
               })
        
        for filename in norm_dict_upload_files.keys():
            dead = norm_dict_upload_files[filename]['D']
            graph_dead['data'].append({'x': list(range(len(dead))), 'y':  dead, 'type': 'scatter', 'name': filename.split('.')[0]}) 



        # grpah total infected all simualation
        graph_tot_inf = dict({'data': [],
                'layout': {'title': 'Comparison total infected at the end of simulation',
                           'yaxis':{'title':'Number of infected'}
                          }
               })
        for filename in norm_dict_upload_files.keys():
            last_day = len(norm_dict_upload_files[filename]['total']) - 1
            total_infeted = norm_dict_upload_files[filename]['total'][last_day] - norm_dict_upload_files[filename]['S'][last_day]
            graph_tot_inf['data'].append({'x': [1], 'y': [total_infeted], 'type': 'bar', 'name': filename.split('.')[0]}) 



        # graph len simulation
        graph_simulation_len = dict({'data': [],
                'layout': {'title': 'Comparison lenght simulation',
                           'xaxis':{'title':'Day'},
                          }
               })

        heatMap_values = []
        heatMap_name = []
        for filename in norm_dict_upload_files.keys():

            sim_len = len(norm_dict_upload_files[filename]['I'])
            infected = [norm_dict_upload_files[filename]['I'][i] + norm_dict_upload_files[filename]['E'][i] for i in range(len(norm_dict_upload_files[filename]['I']))]
            for i in range(len(infected)):
                if infected[i] == 0:
                    sim_len = i
                    break
            graph_simulation_len['data'].append({'y': [filename.split('.')[0]], 'x':  [sim_len], 'type': 'bar', 'name': filename.split('.')[0], 'orientation': 'h'}) 

            #used for heatmap graph
            heatMap_name.append(filename.split('.')[0])
            heatMap_values.append(infected)

        #graph_simulation_len['data'].reverse()
        # reverse to get smae order of other graphics
        heatMap_values.reverse()
        heatMap_name.reverse()

        hovertemplate = "<b> Simulation %{y} Day %{x} <br><br> %{z} Infected"
        heatMap = go.Figure(data=go.Heatmap(
                   z=heatMap_values,
                   y=heatMap_name,
                   hoverongaps = True,
                   name="",
                   hovertemplate = hovertemplate,
                   colorscale = 'YlOrRd'),#'Viridis'),
                   )

        heatMap.update_layout(
            title='Infeted day by day',
            )

        # scatter dead plot
        x_scatter = list()
        y_scatter = list()
        z_scatter = list()
        for filename in norm_dict_upload_files.keys():
            local_x_scatter = []
            local_y_scatter = []
            local_z_scatter = []
            name = filename.split('.')[0]
            last_dead = 0
            count = 0
            for dead in norm_dict_upload_files[filename]['D']:
                if dead != 0 and dead > last_dead:
                    local_x_scatter.append(dead)
                    local_y_scatter.append(name)
                    local_z_scatter.append("Day: " + str(count))
                    last_dead = dead
                count+=1
            
            x_scatter.extend(local_x_scatter)
            y_scatter.extend(local_y_scatter)
            z_scatter.extend(local_z_scatter)

        

        #hovertemplate = "<b> Simulation %{y} Dead %{x} <br><br> %{z} Day"
        scatter_dead = go.Figure()

        scatter_dead.add_trace(go.Scatter(
            x=x_scatter,
            y=y_scatter,
            text=z_scatter,
            name='',
            marker=dict(
                color= x_scatter,
                
                #'#2c82ff',
                #line_color='#2c82ff',
            ),
            mode = "markers"
        ))

        n_tick = int(max(x_scatter)/10)

        scatter_dead.update_traces(mode='markers', marker=dict(line_width=1, symbol='circle', size=16, cmax = max(x_scatter), cmin = min(x_scatter),  colorscale= 'YlOrRd', colorbar=dict(title="")))

        scatter_dead.update_layout(
            title="Comparison dead ",
            xaxis=dict(
                showgrid=False,
                showline=True,
                linecolor='rgb(102, 102, 102)',
                tickfont_color='rgb(102, 102, 102)',
                showticklabels=True,
                dtick=n_tick,
                ticks='outside',
                tickcolor='rgb(102, 102, 102)',
                title ='Dead',
            ),
            margin=dict(l=140, r=40, b=50, t=80),
            paper_bgcolor='white',
            plot_bgcolor='white',
            hovermode='closest',
        )

        y_stack_bar = [filename.split('.')[0] for filename in norm_dict_upload_files.keys()]

        S = []
        E = []
        I = []
        R = []
        D = []

        for file in norm_dict_upload_files.keys():
            last_day = len(norm_dict_upload_files[file]['S']) - 1
            
            S.append(norm_dict_upload_files[file]['S'][last_day])
            E.append(norm_dict_upload_files[file]['E'][last_day])
            I.append(norm_dict_upload_files[file]['I'][last_day])
            R.append(norm_dict_upload_files[file]['R'][last_day])
            D.append(norm_dict_upload_files[file]['D'][last_day])

        #stack_bar

        colors = {'S':'#0000ff', 'E':'#ffa300', 'I':'#ff0000', 'D':'#000000', 'R':'#00ff00'}
        stack_bar = go.Figure()
        stack_bar.add_trace(go.Bar(
            y=y_stack_bar,
            x=S,
            name='S',
            orientation='h',
            marker=dict(
                color= colors['S'],
            )
        ))

        stack_bar.add_trace(go.Bar(
            y=y_stack_bar,
            x=E,
            name='E',
            orientation='h',
            marker=dict(
                color=colors['E'],
            )
        ))

        stack_bar.add_trace(go.Bar(
            y=y_stack_bar,
            x=I,
            name='I',
            orientation='h',
            marker=dict(
                color=colors['I'],
            )
        ))


        stack_bar.add_trace(go.Bar(
            y=y_stack_bar,
            x=R,
            name='R',
            orientation='h',
            marker=dict(
                color=colors['R'],
            
            )
        ))



        stack_bar.add_trace(go.Bar(
            y=y_stack_bar,
            x=D,
            name='D',
            orientation='h',
            marker=dict(
                color=colors['D'],
                )
        ))

        stack_bar.update_layout(barmode='stack', title = 'Summary at the end of simulations')

        
        otuputs = [graph_infected, graph_dead, graph_tot_inf, graph_simulation_len, heatMap, scatter_dead, stack_bar]
        names = ['graph_infected.pdf', 'graph_dead.pdf', 'graph_tot_inf.pdf', 'graph_simulation_len.pdf', 'heatMap.pdf', 'scatter_dead.pdf', 'stack_bar.pdf']

        # to used need to install orca!
        if save_pdf == True:
            for index in range(len(otuputs)):
                if isinstance(otuputs[index], dict):
                    fig = go.Figure(otuputs[index])
                    fig.write_image(names[index])
                else:
                    otuputs[index].write_image(names[index])

        return otuputs



@app.callback([ Output('file-list', 'children'),
                Output('table_parameters', 'children'),
                Output('table_parameters2', 'children'),
                Output('table_parameters3', 'children'),
                Output('alert_div', 'children'),
                
                # graph to return
                Output('graph_comparison_inf', 'figure'),
                Output('graph_comparison_dead', 'figure'),
                Output('graph_comparison_total_inf','figure'),
                Output('graph_simulation_len', 'figure'),
                Output('heatMap', 'figure'),
                Output('scatter_dead', 'figure'),
                Output('stack_bar', 'figure'),

                # view or not view the graph
                Output('graph_comparison_inf', 'style'),
                Output('graph_comparison_dead', 'style'),
                Output('graph_comparison_total_inf', 'style'),
                Output('graph_simulation_len', 'style'),
                Output('heatMap', 'style'),
                Output('scatter_dead', 'style'),
                Output('stack_bar', 'style'),
                ],

              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])

# read all selected files and show comparison 
def update_output(list_of_contents, list_of_names):
    read_error = []
    dict_upload_files = {}
    #print("list_of_names: ", list_of_names)
    
    if list_of_contents is not None:
        for name, data in zip(list_of_names, list_of_contents):
            file_content = parse_contents(name, data)
            if file_content == 'Error':
                print('There was an error processing this file: ' + name)
                read_error.append(name)
            else:
                dict_upload_files[name] = file_content
    
    # no file or only error file
    if len(dict_upload_files.keys()) == 0:
        if len(read_error) > 0:
            alert = dbc.Alert("Can't read this files: " + str(read_error), id = 'alert_id', color="danger",  duration=6000)
        else:
            alert = []
        return [html.Li("No files yet!"), [], [], [], alert, {}, {}, {}, {}, {}, {}, {}, {'display': 'None'}, {'display': 'None'}, {'display': 'None'}, {'display': 'None'}, {'display':'None'}, {'display':'None'},{'display':'None'}]
    
    else:

        graph_infected, graph_dead, graph_tot_inf, graph_simulation_len, heatMap, scatter_dead, stack_bar = create_all_graphs(dict_upload_files, save_pdf = False)
        
        # list updload files
        list_name = [html.Li(filename) for filename in dict_upload_files.keys()]
        
        if len(read_error) == 0:
            alert = dbc.Alert("Succesfully read all files" , id = 'alert_id', color="success",  duration=6000)
        else:
            alert = dbc.Alert("Can't read this files: " + str(read_error), id = 'alert_id', color="danger",  duration=6000)

        table_values = []
        for file in dict_upload_files.keys():
            dict_upload_files[file]['parameters']['sim_name'] = file.split('.')[0]
            table_values.append(dict_upload_files[file]['parameters'])
        
        table = [   
                    html.H4("Simulation parameters"),
                    dash_table.DataTable(
                        columns=[{"name": i, "id": i} for i in ['sim_name','R_0', 'n_of_families', 'number_of_steps', 'incubation_days', 'infection_duration', 'n_initial_infected_nodes']],
                        data= table_values,
                        style_as_list_view=True,
                        style_cell={'padding': '5px'},
                        style_header={
                            'backgroundColor': 'white',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                        {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'
                            }
                        ],
                        sort_action='native',
                        sort_mode="multi",
                    ),
                ]
        table2 = [  
                    html.H4("Restriction parameters"),
                    dash_table.DataTable(
                        columns=[{"name": i, "id": i} for i in ['sim_name', 'initial_day_restriction', 'restriction_duration', 'social_distance_strictness', 'restriction_decreasing']],
                        data=table_values,
                        #style_cell={'textAlign': 'left'},
                        #style_as_list_view=True,
                        style_as_list_view=True,
                        style_cell={'padding': '5px'},
                        style_header={
                            'backgroundColor': 'white',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                        {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'
                            }
                        ],
                        sort_action='native',
                        sort_mode="multi",
                    ),
                ] 
        table3 = [
                    html.H4("Testing and quaratine parameters"),
                    dash_table.DataTable(
                        columns=[{"name": i, "id": i} for i in ['sim_name', 'n_test', 'policy_test', 'contact_tracing_efficiency', 'contact_tracing_duration']],
                        data=table_values,
                        #style_cell={'textAlign': 'left'},
                        #style_as_list_view=True,
                        style_as_list_view=True,
                        style_cell={'padding': '5px'},
                        style_header={
                            'backgroundColor': 'white',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                        {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'
                            }
                        ],
                        sort_action='native',
                        sort_mode="multi",
                    ),
                        

        ]  
        
        #returns
        return [list_name, table, table2, table3, alert, graph_infected, graph_dead, graph_tot_inf, graph_simulation_len, heatMap, scatter_dead, stack_bar, {'display': 'block'}, {'display': 'block'}, {'display': 'block'}, {'display': 'block'}, {'display': 'block'}, {'display': 'block'}, {'display': 'block'}]

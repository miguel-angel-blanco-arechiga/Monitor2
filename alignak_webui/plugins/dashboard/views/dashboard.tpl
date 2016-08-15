%setdefault('debug', False)

%from bottle import request
%rebase("layout", js=['dashboard/htdocs/js/lodash.js', 'dashboard/htdocs/js/jquery.ui.touch-punch.min.js', 'dashboard/htdocs/js/gridstack.min.js'], css=['dashboard/htdocs/css/dashboard.css', 'dashboard/htdocs/css/gridstack.min.css'], title=title)


<style type="text/css">
   .grid-stack {
   }

   .grid-stack-item-content {
   }
</style>

<div id="dashboard">
%if debug:
   <div class="panel-group">
      <div class="panel panel-default">
         <div class="panel-heading">
            <h4 class="panel-title">
               <a data-toggle="collapse" href="#collapse_widgets"><i class="fa fa-bug"></i> Dashboard installed widgets</a>
            </h4>
         </div>
         <div id="collapse_widgets" class="panel-collapse collapse">
            %for widget in dashboard_widgets:
            <h4>{{widget['name']}}</h4>
            <dl class="dl-horizontal" style="height: 200px; overflow-y: scroll;">
               %for k,v in sorted(widget.items()):
                  <dt>{{k}}</dt>
                  <dd>{{v}}</dd>
               %end
            </dl>
            %end
         </div>
      </div>
   </div>
%end
   <div id="dashboard-synthesis" class="row col-sm-offset-2 col-xs-offset-1">
      <div class="col-sm-2 col-xs-5">
         %hs = datamgr.get_livesynthesis()['hosts_synthesis']
         %if hs:
         %font='danger' if hs['pct_problems'] >= hs['critical_threshold'] else 'warning' if hs['pct_problems'] >= hs['warning_threshold'] else 'success'
         %from alignak_webui.objects.element_state import ElementState
         %cfg_state = ElementState().get_icon_state('host', 'up')
         %icon = cfg_state['icon']
         <center>
            <a href="{{ webui.get_url('Livestate table') }}?search=type:host">
               <span class="fa fa-4x fa-{{icon}} icon-{{font}}"></span>
               <span class="icon-title"><span class="fa fa-plus"></span>&nbsp;{{_('Hosts')}}</span>
               <span class="icon-badge icon-badge-left icon-badge-info" title="{{_('Number of monitored hosts')}}">{{hs["nb_elts"]}}</span>
               <span class="icon-badge icon-badge-right icon-badge-{{font}}" title="{{_('Number of hosts in problem')}}">{{hs["nb_problems"]}}</span>
            </a>
         </center>
         %end
      </div>
      <div class="col-sm-2 col-xs-5">
         %ss = datamgr.get_livesynthesis()['services_synthesis']
         %if ss:
         %font='danger' if ss['pct_problems'] >= ss['critical_threshold'] else 'warning' if ss['pct_problems'] >= ss['warning_threshold'] else 'success'
         %from alignak_webui.objects.element_state import ElementState
         %cfg_state = ElementState().get_icon_state('service', 'ok')
         %icon = cfg_state['icon']
         <center>
            <a class="icon-{{font}}" href="{{ webui.get_url('Livestate table') }}?search=type:service">
               <span class="fa fa-4x fa-{{icon}} icon-{{font}}"></span>
               <span class="icon-title"><span class="fa fa-plus"></span>&nbsp;{{_('Services')}}</span>
               <div class="icon-badge icon-badge-left icon-badge-info" title="{{_('Number of hosts up')}}">{{ss["nb_elts"]}}</div>
               <div class="icon-badge icon-badge-right icon-badge-{{font}}" title="{{_('Number of services in problems')}}">{{ss["nb_problems"]}}</div>
            </a>
         </center>
         %end
      </div>
      <div class="col-sm-2 col-xs-5">
         %if hs and ss:
         %problems = hs['nb_problems'] + ss['nb_problems']
         %elements = hs['nb_elts'] + ss['nb_elts']
         %pct_problems = round(100.0 * problems / elements, 2) if elements else 0.0
         %font='danger' if pct_problems >= hs['global_critical_threshold'] else 'warning' if pct_problems >= hs['global_warning_threshold'] else 'success'
         <center>
            <a href="{{ webui.get_url('Livestate table') }}?search=state_id:1 state_id:2">
               <span class="fa fa-4x fa-exclamation-triangle icon-{{font}}"></span>
               <span class="icon-title"><span class="fa fa-plus"></span>&nbsp;{{_('Problems')}}</span>
               <span class="icon-badge icon-badge-left icon-badge-info" title="{{_('Number of monitored items')}}">{{hs["nb_elts"] + ss["nb_elts"]}}</span>
               <span class="icon-badge icon-badge-right icon-badge-{{font}}" title="{{_('Number of problems')}}">{{hs["nb_problems"] + ss["nb_problems"]}}</span>
            </a>
         </center>
         %end
      </div>
      <div class="col-sm-2 col-xs-5">
         %if hs and ss:

         %# TO BE REPLACED WITH IMPACTS DATA ...

         %problems = hs['nb_problems'] + ss['nb_problems']
         %elements = hs['nb_elts'] + ss['nb_elts']
         %pct_problems = round(100.0 * problems / elements, 2) if elements else 0.0
         %font='info'
         <center>
            <a href="{{ webui.get_url('Livestate table') }}">
               <span class="fa fa-4x fa-bolt icon-{{font}}"></span>
               <span class="icon-title"><span class="fa fa-plus"></span>&nbsp;{{_('Impacts')}}</span>
               <span class="icon-badge icon-badge-left icon-badge-info" title="{{_('Number of monitored items')}}">{{hs["nb_elts"] + ss["nb_elts"]}}</span>
               <span class="icon-badge icon-badge-right icon-badge-{{font}}" title="{{_('Number of problems')}}">{{hs["nb_problems"] + ss["nb_problems"]}}</span>
            </a>
         </center>
         %end
      </div>
   </div>

   %if current_user.can_change_dashboard() and not len(dashboard_widgets):
   <div id="propose-widgets" class="panel panel-warning" style="margin:10px; display:none">
      <div class="panel-body" style="padding-bottom: -10">
         <center>
            <h3>{{_('You do not have any widgets yet ...')}}</h3>
         </center>
         <hr/>
         <p>
            {{_('Click the ')}}
            <strong>{{_('Add a new widget')}}</strong>
            {{_(' buttton in the menu to list all the available widgets.')}}
         </p>
         <p>
            {{_('Select a proposed widget to view its description.')}}
         </p>
         <p>
            {{_('Click the ')}}
            <strong>{{_('Add widget')}}</strong>
            {{_(' button on top of the description to include the widget in your dashboard.')}}
         </p>
      </div>
   </div>
   %end

   <div class="container-fluid">
      <!-- Widgets loading indicator -->
      <div id="widgets_loading"></div>

      <!-- Widgets grid -->
      <div class="grid-stack">
         %for widget in dashboard_widgets:
            <div class="grid-stack-item"
                  id="{{widget['id']}}"
                  data-uri="{{widget['uri']}}"
                  data-name="{{widget['name']}}"
                  data-icon="{{widget['icon']}}"
                  data-template="{{widget['template']}}"

                  data-gs-id="{{widget['id']}}"
                  data-gs-x="{{widget['x']}}"
                  data-gs-y="{{widget['y']}}"
                  data-gs-width="{{widget['width']}}"
                  data-gs-min-width="{{widget['minWidth']}}"
                  data-gs-max-width="{{widget['maxWidth']}}"
                  data-gs-height="{{widget['height']}}"
                  data-gs-min-height="{{widget['minHeight']}}"
                  data-gs-max-height="{{widget['maxHeight']}}"
                  >
               <div class="grid-stack-item-content">
               </div>
            </div>
         %end
      </div>
   </div>
</div>
<script type="text/javascript">
   var dashboard_logs = false;

   $('.grid-stack').on('change', function (e, items) {
      if (dashboard_logs) console.log("Grid layout changed:", items);
      if (items === undefined) return;
      var widgets = [];
      for (i = 0; i < items.length; i++) {
         if (dashboard_logs) console.log("Grid item: ", $('#'+items[i].id));
         var widget = {
            'id': items[i].id,
            'uri': $('#'+items[i].id).data('uri'),
            'name': $('#'+items[i].id).data('name'),
            'icon': $('#'+items[i].id).data('icon'),
            'template': $('#'+items[i].id).data('template'),
            'x': items[i].x,
            'y': items[i].y,
            'width': items[i].width,
            'minWidth': items[i].minWidth,
            'maxWidth': items[i].maxWidth,
            'height': items[i].height,
            'minHeight': items[i].minHeight,
            'maxHeight': items[i].maxHeight
         };
         var found = widgets.some(function (el) {
            return el.id === widget.id;
         });
         if (!found) {
            widgets.push(widget);
         }
      }
      if (widgets.length > 0) {
         var to_save = {'widgets': widgets}
         save_user_preference('{{widgets_place}}_widgets', JSON.stringify(to_save), function(){
            if (dashboard_logs) console.log("Saved {{widgets_place}} widgets grid", to_save)
         });
      }
   });

   $('.grid-stack').on('removed', function(event, items) {
      for (var i = 0; i < items.length; i++) {
         if (dashboard_logs) console.log('Item removed from grid:', items[i]);
      }
   });

   $(document).ready(function(){
      set_current_page("{{ webui.get_url(request.route.name) }}");

      %if message:
         raise_message_{{message.get('status', 'ko')}}("{{! message.get('message')}}");
      %end

      %if not len(dashboard_widgets):
         // Show the widgets proposal area.
         $('#propose-widgets').show();
      %else:
         // Hide the widgets proposal area ...
         $('#propose-widgets').hide();

         // Loading indicator ...
         $("#widgets_loading").
            html('<i class="fa fa-spinner fa-spin fa-3x"></i> <span class="lead">{{_('Loading widgets ... ')}}</span>').
            show();

         nb_widgets_loading = 0;
      %end

      var options = {
         float: false,
         animate: true,
         cellHeight: 20,
         disableDrag: false,
         disableResize: false,
         removable: true,
         verticalMargin: 20,
         alwaysShowResizeHandle: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
         resizable: {
            handles: 'e, se, s, sw, w'
         }
      };
      $('.grid-stack').gridstack(options);

      %for widget in dashboard_widgets:
         // We are saying to the user that we are loading a widget with
         // a spinner
         nb_widgets_loading += 1;

         if (dashboard_logs) console.log("Load: {{widget['uri']}} for {{widget['id']}}")
         $("#{{widget['id']}} div.grid-stack-item-content").load(
            "{{widget['uri']}}",
            {
               %for (key, v) in widget['options'].iteritems():
                  {{key}}: '{{v.get('value', '')}}',
               %end
               title: '{{widget['name']}}',
               widget_template: '{{widget['template']}}',
               widget_id: '{{widget['id']}}'
            },
            function(response, status, xhr) {
               nb_widgets_loading -= 1;
               if (nb_widgets_loading==0){
                  $('#widgets_loading').hide();
               }

               if ( status == "error" ) {
                  raise_message_ko(status, data);
               }
            }
         );

      %end
   });
</script>

%setdefault('debug', False)

%setdefault('commands', False)

%from bottle import request
%search_string = request.query.get('search', '')

%rebase("layout", title=title, js=[], css=[], pagination=pagination, page="/contacts")

<!-- contacts filtering and display -->
<div id="contacts">
   %if debug:
   <div class="panel-group">
      <div class="panel panel-default">
         <div class="panel-heading">
            <h4 class="panel-title">
               <a data-toggle="collapse" href="#collapse1"><i class="fa fa-bug"></i> Contacts as dictionaries</a>
            </h4>
         </div>
         <div id="collapse1" class="panel-collapse collapse">
            <ul class="list-group">
               %for contact in contacts:
                  <li class="list-group-item"><small>Contact: {{contact}} - {{contact.__dict__}}</small></li>
               %end
            </ul>
            <div class="panel-footer">{{len(contacts)}} elements</div>
         </div>
      </div>
   </div>
   %end

   <div class="panel panel-default">
      %if commands and current_user.is_administrator():
      <div class="panel-heading">
         <div class="btn-toolbar" role="toolbar" aria-label="{{_('Users commands')}}">
            <div class="btn-group btn-lg" role="group" data-type="actions" aria-label="{{_('Users commands')}}">
               <button class="btn btn-default"
                     data-type="action" data-action="add-user"
                     data-toggle="tooltip" data-placement="bottom" title="{{_('Create a new user')}}"
                     >
                     <i class="fa fa-plus"></i>
                     {{_('Add a new user')}}
               </button>
            </div>
         </div>
      </div>
      %end

      <div class="panel-body">
      %if not contacts:
         %include("_nothing_found.tpl", search_string=search_string)
      %else:

         %# First element for global data
         %object_type, start, count, total, dummy = pagination[0]
         <i class="pull-right small">{{_('%d elements out of %d') % (count, total)}}</i>

         <table class="table table-condensed">
            <thead><tr>
               <th width="40px"></th>
               <th>{{_('Name')}}</th>
               <th>{{_('Username')}}</th>
               <th>{{_('Administrator')}}</th>
               <th>{{_('Commands')}}</th>
               <th>{{_('Widgets')}}</th>
               %if commands and current_user.can_submit_commands():
               <th class="hidden-sm hidden-xs" width="50px">{{_('Commands')}}</th>
               %end
            </tr></thead>

            <tbody>
            %for contact in contacts:
               <tr data-toggle="collapse" data-target="#details-{{contact.get_id()}}" class="accordion-toggle">
                  <td>
                     {{! contact.get_html_state()}}
                  </td>

                  <td>
                     <small data-toggle="tooltip" data-placement="top" title="{{contact.get_description()}}">{{contact.get_name()}}</small>
                  </td>

                  <td>
                     <small data-toggle="tooltip" data-placement="top" title="{{contact.get_description()}}">{{contact.get_username()}}</small>
                  </td>

                  <td>
                     <small>{{! webui.helper.get_on_off(status=contact.is_administrator())}}</small>
                  </td>

                  <td>
                     <small>{{! webui.helper.get_on_off(contact.can_submit_commands())}}</small>
                  </td>

                  <td>
                     <small>{{! webui.helper.get_on_off(contact.can_change_dashboard())}}</small>
                  </td>

                  %if commands and current_user.can_submit_commands():
                  <td align="right">
                     <div class="navbar" role="toolbar" aria-label="{{_('Select a user to change dashboard layout')}}">
                        <form class="form-inline" role="search">
                           <!-- Open a session for this service -->
                           <div class="btn-group" role="group" data-type="actions" aria-label="{{_('User actions')}}">
                              <button class="btn btn-default btn-sm navbar-btn"
                                   data-type="action" data-action="delete-user"
                                   data-toggle="tooltip" data-placement="bottom" title="{{_('Delete this user')}}"
                                   data-element="{{user.get_id()}}"
                                   >
                                   <i class="fa fa-remove"></i>
                              </button>
                              <button class="btn btn-default btn-sm navbar-btn"
                                   data-type="action" data-action="edit-user"
                                   data-toggle="tooltip" data-placement="bottom" title="{{_('Edit this user')}}"
                                   data-element="{{user.get_id()}}"
                                   >
                                   <i class="fa fa-edit"></i>
                              </button>
                           </div>
                        </form>
                     </div>
                  </td>
                  %end
               </tr>
            %end
            </tbody>
         </table>
      %end
      </div>
   </div>
 </div>

 <script>
   $(document).ready(function(){
      set_current_page("{{ webui.get_url(request.route.name) }}");
   });
 </script>
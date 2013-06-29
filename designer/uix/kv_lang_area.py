import re

from kivy.uix.textinput import TextInput
from kivy.properties import BooleanProperty, StringProperty, NumericProperty, OptionProperty
from kivy.app import App
from kivy.lang import Builder
from kivy.factory import Factory

def get_indent_str(indentation):
    i = 0
    s = ''
    while i < indentation:
        s += ' '
        i += 1
    
    return s

def get_line_end_pos(string, line):
    _line = 0
    _line_pos = -1
    _line_pos = string.find('\n', _line_pos + 1)
    while _line < line:
        _line_pos = string.find('\n', _line_pos + 1)
        _line += 1
    
    return _line_pos

def get_line_start_pos(string, line):
    _line = 0
    _line_pos = -1
    _line_pos = string.find('\n', _line_pos + 1)
    while _line < line - 1:
        _line_pos = string.find('\n', _line_pos + 1)
        _line += 1
    
    return _line_pos

def get_indent_level(string):
    lines = string.splitlines()
    lineno = 0
    line = lines[lineno]
    indent = 0
    total_lines = len(lines)
    while line < total_lines and indent == 0:
        indent = len(line)-len(line.lstrip())
        line = lines[lineno]
        line += 1
    
    return indent

def get_indentation(string):
    count = 0
    for s in string:
        if s == ' ':
            count+=1
        else:
            return count
    
    return count


class KVLangArea(TextInput):
    clicked  = BooleanProperty(False)
    have_error = BooleanProperty(False)
    _reload = BooleanProperty(False)
    __events__=('on_show_edit',)

    def on_show_edit(self, *args):
        pass

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.clicked = True
            self.dispatch('on_show_edit')

        return super(KVLangArea, self).on_touch_down(touch)
    
    def _get_widget_path(self, widget):
        '''To get path of a widget, path of a widget is a list containing 
           the index of it in its parent's children list. For example,
           Widget1:
               Widget2:
               Widget3:
                   Widget4:
           
           path of Widget4 is [0, 1, 0]
        '''

        path_to_widget = []
        _widget = widget
        while _widget != App.get_running_app().root.playground.sandbox:
            place = len(_widget.parent.children) - _widget.parent.children.index(_widget) - 1
            path_to_widget.append(place)
            _widget = _widget.parent

        return path_to_widget

    def add_widget_to_parent(self, widget, target):
        '''This function is called when widget is added to target.
           It will search for line where parent is defined in text and will add
           widget there.
        '''

        path_to_widget = self._get_widget_path(widget.parent)
        path_to_widget.reverse()
        
        text = re.sub(r'#.+', '', self.text)

        lines = text.splitlines()
        total_lines = len(lines)
        parent_lineno = self._find_widget_place(path_to_widget, lines,
                                                total_lines, 1)

        if parent_lineno >= total_lines:
            return
        
        #Get text of parents line
        parent_line = lines[parent_lineno]
        insert_after_line = -1
        if parent_line.find(':') == -1:
            #If parent_line doesn't contain ':' then insert it
            #Also insert widget's rule after its properties
            insert_after_line = parent_line
            _line = 0         
            _line_pos = -1
            _line_pos = self.text.find('\n', _line_pos + 1)
            while _line <= insert_after_line:
                _line_pos = self.text.find('\n', _line_pos + 1)
                _line += 1

            self.text = self.text[:_line_pos] + ':' + self.text[_line_pos:]
                
        else:
            #If ':' in parent_line then, find a place to insert widget's rule
            indent = len(parent_line) - len(parent_line.lstrip())
            lineno = parent_lineno
            _indent = indent +1
            line = parent_line
            while (line.strip() == '' or _indent > indent):
                lineno += 1
                if lineno >= total_lines:
                    break
                line = lines[lineno]
                _indent = len(line) - len(line.lstrip())

            insert_after_line = lineno - 1
            line = lines[insert_after_line]
            while line.strip() == '':
                insert_after_line -= 1
                line = lines[insert_after_line]

        if insert_after_line == total_lines - 1:
            #if inserting at the last line
            _line_pos = len(self.text) - 1
            self.text = self.text[:_line_pos + 1] + '\n' + \
                get_indent_str(indent + 4) + type(widget).__name__ + ':'
        else:
            #inserting somewhere else
            insert_after_line -= 1
            _line = 0         
            _line_pos = -1
            _line_pos = self.text.find('\n', _line_pos + 1)
            while _line <= insert_after_line:
                _line_pos = self.text.find('\n', _line_pos + 1)
                _line += 1

            self.text = self.text[:_line_pos] + '\n' + \
                get_indent_str(indent + 4) + type(widget).__name__ + ':' + \
                self.text[_line_pos:]
    
    def remove_widget_from_parent(self, widget, parent):
        '''This function is called when widget is removed from parent.
           It will delete widget's rule from parent's rule
        '''

        path_to_widget = self._get_widget_path(widget)
        path_to_widget.reverse()
        
        #Go to widget's rule's line and determines all its rule's
        #and it's child if any. Then delete them
        text = re.sub(r'#.+', '', self.text)
        lines = text.splitlines()
        total_lines = len(lines)
        widget_lineno = self._find_widget_place(path_to_widget, lines, total_lines, 1)
        widget_line = lines[widget_lineno]
        indent = len(widget_line) - len(widget_line.lstrip())
        lineno = widget_lineno
        _indent = indent +1
        line = widget_line
        while (line.strip() == '' or _indent > indent):
            lineno += 1
            if lineno >= total_lines:
                break
            line = lines[lineno]
            _indent = len(line) - len(line.lstrip())

        delete_until_line = lineno - 1
        line = lines[delete_until_line]
        while line.strip() == '':
            delete_until_line -= 1
            line = lines[delete_until_line]

        widget_line_pos = get_line_start_pos(self.text, widget_lineno)
        delete_until_line_pos = get_line_end_pos(self.text, delete_until_line)
        
        self._reload = False
        self.text = self.text[:widget_line_pos] + self.text[delete_until_line_pos:]
    
    def _get_widget_from_path(self, path):
        '''This function is used to get widget given its path
        '''

        if not App.get_running_app().root.playground.root:
            return None

        if len(path) == 0:
            return None

        root = App.get_running_app().root.playground.root
        path_index = 0
        widget = root
        path_length = len(path)

        while path_index < path_length:
            widget = widget.children[len(widget.children) - 1 - path[path_index]]
            path_index += 1
        
        return widget

    def on_text(self, *args):
        '''This function is called whenever text changes
        '''

        if self.text == '':
            return
        
        lines = re.sub(r'#.+', '', self.text).splitlines()
        if self.cursor[1] < 0 or self.cursor[1] >= len(lines):
            return
        
        if not self._reload:
            self._reload = True
            return

        statusbar = App.get_running_app().root.statusbar
        
        #Determine the widget inside which cursor is present
        path_to_widget = self._get_widget_path_at_line(self.cursor[1])
        widget = self._get_widget_from_path(path_to_widget)

        line = lines[self.cursor[1]]
        colon_pos = line.find(':')
        #if ':' in line, then either property is modified or added or
        #widget's class is modified
        if colon_pos != -1:
            if colon_pos != len(line.rstrip()) - 1:
                #A property is modified or added
                value = line[colon_pos+1:].strip()
                if value.strip() == '':
                    return

                prop = line[:colon_pos].strip()
                try:
                    if isinstance(widget.properties()[prop], NumericProperty):
                        if value == 'None':
                            value = None
                        else:
                            value = float(value)
    
                    elif isinstance(widget.properties()[prop], StringProperty):
                        value = value.replace('"','').replace("'","")
    
                    elif isinstance(widget.properties()[prop], BooleanProperty):
                        if value == 'False':
                            value = False
                        elif value == 'True':
                            value = True
    
                    elif isinstance(widget.properties()[prop], OptionProperty):
                        value = value.replace('"','').replace("'","")

                    else:
                        return
    
                    setattr(widget, prop, value)
                    self.have_error = False
                    statusbar.show_message("")

                except:
                    self.have_error = True
                    statusbar.show_message("Cannot set '%s' to '%s'"%(value, prop))

        else:
            #A widget is added or removed
            playground = App.get_running_app().root.playground
            project_loader = App.get_running_app().root.project_loader
            try:
                widget = project_loader.reload_root_widget_from_str(self.text)
                if widget:
                    playground.remove_widget_from_parent(playground.root, None, from_kv=True)
                    playground.add_widget_to_parent(widget, None, from_kv=True)
                statusbar.show_message("")
                self.have_error = False

            except:
                self.have_error = True
                statusbar.show_message("Cannot reload from text")

    def _get_widget_path_at_line(self, lineno):
        '''To get widget path of widget at line
        '''

        if self.text == '':
            return []
        
        text = self.text
        #Remove all comments
        text = re.sub(r'#.+', '', text)

        lines = text.splitlines()
        line = lines[lineno]
        
        #Search for the line containing widget's name
        _lineno = lineno

        while line.find(':') != -1 and line.strip().find(':') != len(line.strip()) - 1:
            lineno -= 1
            line = lines[lineno]

        path = []
        child_count = 0
        #From current line go above and 
        #fill number of children above widget's rule
        while _lineno >= 0 and lines[_lineno].strip() != "" and get_indentation(lines[lineno]) != 0:
            _lineno = lineno - 1
            diff_indent = get_indentation(lines[lineno]) - \
                          get_indentation(lines[_lineno])

            while _lineno >= 0 and (lines[_lineno].strip() == '' \
                                    or diff_indent <= 0):
                if lines[_lineno].strip() != '' and diff_indent == 0 and \
                    'canvas' not in lines[_lineno] and \
                        (lines[_lineno].find(':') == -1 or 
                         lines[_lineno].find(':') == len(lines[_lineno].rstrip())- 1):
                    child_count += 1

                _lineno -= 1
                diff_indent = get_indentation(lines[lineno]) - \
                              get_indentation(lines[_lineno])

            lineno = _lineno
            
            if _lineno > 0:
                _lineno += 1

            if 'canvas' not in lines[_lineno] and \
                lines[_lineno].strip().find(':') == len(lines[_lineno].strip()) -1:

                path.insert(0, child_count)
                child_count = 0

        return path
        
    def set_property_value(self, widget, prop, value, proptype):
        '''To find and change the value of property of widget rule in text
        '''
        
        #Do not add property if value is empty and 
        #property is not a string property
        if not isinstance(widget.properties()[prop], StringProperty) and\
            value == '':
            return

        path_to_widget = self._get_widget_path(widget)
        path_to_widget.reverse()
        
        #Go to the line where widget is declared
        lines = re.sub(r'#.+', '', self.text).splitlines()
        total_lines = len(lines)
        widget_lineno = self._find_widget_place(path_to_widget, lines, total_lines, 1)
        widget_line = lines[widget_lineno]
        indent = get_indentation(widget_line)
        prop_found = False

        if ':' not in widget_line:
            #If cannot find ':' then insert it
            self.cursor = (len(lines[widget_lineno]), widget_lineno)
            lines[widget_lineno] += ':'
            self.insert_text(':')

        else:
            #Else find if property has already been declared with a value
            lineno = widget_lineno + 1
            line = lines[lineno]
            _indent = get_indentation(line)
            colon_pos = -1
            while lineno < total_lines and (line.strip() == '' or _indent > indent):
                line = lines[lineno]
                _indent = get_indentation(line)
                if line.strip() != '':
                    colon_pos = line.find(':')
                    if colon_pos == -1:
                        break
                    
                    if colon_pos == len(line.rstrip()) - 1:
                        break
                    
                    if prop == line[:colon_pos].strip():
                        prop_found = True
                        break

                lineno += 1
        
        if prop_found:
            #if property found then change its value
            _pos_prop_value = get_line_start_pos(self.text, lineno) + colon_pos + 2
            _line_end_pos = get_line_end_pos(self.text, lineno)
            if proptype == 'StringProperty':
                value = "'"+value+"'"
            self.text = self.text[:_pos_prop_value] + ' ' + str(value) + \
                self.text[_line_end_pos:]

            self.cursor = (0, lineno)

        else:
            #if not found then add property after the widgets line
            _line_start_pos = get_line_start_pos(self.text, widget_lineno)
            _line_end_pos = get_line_end_pos(self.text, widget_lineno)
            if proptype == 'StringProperty':
                value = "'"+value+"'"
            indent_str = '\n'
            for i in range(indent + 4):
                indent_str += ' '
            
            self.cursor = (len(lines[widget_lineno]), widget_lineno)
            self.insert_text(indent_str + prop+ ': ' + str(value))

    def _find_widget_place(self, path, lines, total_lines, lineno, indent = 4):
        '''To find the line where widget is declared according to path
        '''

        child_count = 0
        path_index = 1
        path_length = len(path)
        #From starting line go down to find the widget's rule according to path
        while lineno < total_lines and path_index < path_length:
            line = lines[lineno]
            _indent = get_indentation(line)
            colon_pos = line.find(':')
            if _indent == indent and line.strip() != '':
                if colon_pos != -1:
                    line = line.rstrip()
                    if colon_pos == len(line) - 1 and 'canvas' not in line:
                        line = line[:colon_pos].lstrip()                            
                        if child_count == path[path_index]:
                            path_index += 1
                            indent = _indent + 4
                            child_count = 0
                        else:
                            child_count += 1
                else:
                    child_count += 1

            lineno += 1

        return lineno - 1
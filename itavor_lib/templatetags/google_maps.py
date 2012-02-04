from django import template
from django.template import Library
from django.template import RequestContext
from django.template import resolve_variable
from django.utils.safestring import SafeString
from django.conf import settings

register = Library()

INCLUDE_TEMPLATE = """
<script src="http://maps.google.com/maps?file=api&v=2&key=%s" type="text/javascript"></script>
""" % settings.GOOGLE_MAPS_API_KEY

BASIC_TEMPLATE = """
<div id="map_%s" style="width: %spx; height: %spx"></div>
<script>
function create_map_%s() {
   if (GBrowserIsCompatible()) {
    var map = new GMap2(document.getElementById("map_%s"));
    map.enableDoubleClickZoom();
    map.enableContinuousZoom();
    map.addControl(new GSmallMapControl());
    map.addControl(new GMapTypeControl());
    map.setCenter(new GLatLng(%s,%s), %s, map.getMapTypes()[%d]);

    var point = map.getCenter();
    var m = new GMarker(point);
    GEvent.addListener(m, "click", function() {
       m.openInfoWindowHtml("%s");
    });
    map.addOverlay(m);
    return map;
   }
}
</script>
"""
# {% gmap name:mimapa width:300 height:300 latitude:x longitude:y zoom:20 view:hybrid %} Message for a marker at that point {% endgmap %}

class GMapNode (template.Node):
    def __init__(self, params, nodelist):
        self.params = params
        self.nodelist = nodelist
        
    def render (self, context):
        for k,v in self.params.items():
            try:
                self.params[k] = resolve_variable(v, context)
            except:
                pass
            if k == "view":
                if v=="satellite": 
                    v = 1
                elif v=="map":
                    v = 0
                else:
                    v = 2
                self.params[k] = v
        self.params["message"] = self.nodelist.render(context).replace("\n", "<br />")
        html = BASIC_TEMPLATE % (self.params['name'], self.params['width'], self.params['height'], self.params['name'], self.params['name'], self.params['latitude'], self.params['longitude'], self.params['zoom'], self.params['view'], self.params['message'])
        return SafeString(html)

def do_gmap(parser, token):
    items = token.split_contents()

    nodelist = parser.parse(('endgmap',))
    parser.delete_first_token()
    
    #Default values 
    parameters={
            'name'      : "default",
            'width'     : "300",
            'height'    : "300",
            'latitude'  : "33",
            'longitude' : "-3",
            'zoom'      : "15",
            'view'      : "hybrid", # map, satellite, hybrid
            'message'   : "No message",
    }
    for item in items[1:]:
        param, value = item.split(":")
        param = param.strip()
        value = value.strip()
        
        if parameters.has_key(param):
            if value[0]=="\"":
                value = value[1:-1]
            parameters[param] = value
        
    return GMapNode(parameters, nodelist)

class GMapScriptNode (template.Node):
    def render (self, context):
        return SafeString(INCLUDE_TEMPLATE)

def do_gmap_script(parser, token):
    try:
        tag_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%s tag takes no arguments" % token.contents[0])
    return GMapScriptNode()

register.tag('gmap', do_gmap)
register.tag('gmap-script', do_gmap_script)

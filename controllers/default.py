# -*- coding: utf-8 -*-
### required - do no delete
def user(): return dict(form=auth())
def download(): return response.download(request,db)
def call(): return service()
### end requires
def index():
    return dict()

def error():
    return dict()

def browse_images():
    from pmc_turbo.ground.ground_index import get_file_index
    from pmc_turbo.communication.file_format_classes import JPEGFile
    mi = get_file_index(data_dir_glob='/data/pmc/piggyback_gse_data/2*')
    dd = mi.df[mi.df.file_type==JPEGFile.file_type]
    image_table = dd.iloc[-25:]
    image_table.sort_values(by='last_timestamp',ascending=False,inplace=True)
    return dict(image_table=image_table)

def image():
    print request.vars.filename
    if request.vars.filename:
        from pmc_turbo.communication.file_format_classes import load_and_decode_file
        result = load_and_decode_file(request.vars.filename)
        return result.payload
    return request.vars


def leader_short_status():
    from pmc_turbo.ground.lowrate_monitor import LowrateMonitor
    lrm = LowrateMonitor()
    return dict(lrm.latest(254)[0])

def camera_short_status():
    from pmc_turbo.ground.lowrate_monitor import LowrateMonitor
    from pmc_turbo.ground.short_status_format import format_short_status_camera, get_item_name
    from collections import OrderedDict
    lrm = LowrateMonitor()
    result = OrderedDict()
    for k, v in lrm.latest(4)[0].items():
        value, format = format_short_status_camera(k,v)
        print k, value, format
        if format == 'r':
            value = TD(value,_style="color:red")
        else:
            value = TD(value,_style="align:right")
        result[get_item_name(k)] = value
    items = result.items()
    num_cols = 3
    rows = []
    this_row = []
    for k,v in items:
        this_row.append(TD(TABLE(TR(TD(k),v))))
        if len(this_row) == num_cols:
            rows.append(TR(*this_row))
            this_row = []
    return dict(short_status=TABLE(*rows))
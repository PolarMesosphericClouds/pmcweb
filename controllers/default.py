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

def _fix_filename(filename):
    import os
    if os.path.exists(filename):
        return filename
    return filename.replace('/data','/data/pmc')

def browse_image_directories():
    import glob
    data_dirs = glob.glob('/data/piggyback_gse_data/2*')
    data_dirs.sort(reverse=True)
    return dict(data_dirs=data_dirs)

def browse_images():
    from pmc_turbo.ground.ground_index import get_file_index
    from pmc_turbo.communication.file_format_classes import JPEGFile
    if request.vars.directory:
        directory= request.vars.directory
    else:
        directory = '/data/piggyback_gse_data/2*'
    mi = get_file_index(data_dir_glob=directory)
    dd = mi.df[mi.df.file_type==JPEGFile.file_type]
    start_from_end = True
    try:
        latest_timestamp = int(request.vars.latest_frame_timestamp)
        dd = dd[dd.frame_timestamp_ns < latest_timestamp]
        start_from_end = True
    except Exception:
        pass
    try:
        earliest_timestamp = int(request.vars.earliest_frame_timestamp)
        dd = dd[dd.frame_timestamp_ns > earliest_timestamp]
        start_from_end = False
    except Exception:
        pass

    num_images_per_page = 25
    try:
        num_images_per_page = int(request.vars.num_images_per_page)
    except Exception:
        pass
    if start_from_end:
        image_table = dd.iloc[-num_images_per_page:]
    else:
        image_table = dd.iloc[:num_images_per_page]
    oldest_timestamp = image_table.frame_timestamp_ns.min()
    if request.vars.latest_frame_timestamp:
        newest_timestamp = dd.frame_timestamp_ns.max()
    else:
        newest_timestamp = None
    image_table = image_table.sort_values(by='last_timestamp',ascending=False)
    return dict(image_table=image_table, next_url=URL("browse_images",vars=dict(earliest_frame_timestamp=newest_timestamp,
                                                                                num_images_per_page=num_images_per_page,
                                                                                directory=directory)),
                previous_url=URL("browse_images", vars=dict(latest_frame_timestamp=oldest_timestamp,
                                                            num_images_per_page=num_images_per_page,
                                                            directory=directory)))

def image():
    print request.vars.filename
    if request.vars.filename:
        from pmc_turbo.communication.file_format_classes import load_and_decode_file
        filename = _fix_filename(request.vars.filename)
        print filename
        result = load_and_decode_file(filename)
        return result.payload
    return request.vars

def view_image():
    print request.vars.filename
    if request.vars.filename:
        from pmc_turbo.communication.file_format_classes import load_and_decode_file
        filename = _fix_filename(request.vars.filename)
        print filename
        result = load_and_decode_file(filename)
        parameters = dict([(k,getattr(result,k)) for k in result._metadata_parameter_names])
        return dict(parameters=parameters, filename=request.vars.filename)
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
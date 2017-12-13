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

def short_status():
    from pmc_turbo.communication.short_status import load_short_status_from_payload,load_short_status_from_file
    from pmc_turbo.communication.file_format_classes import load_and_decode_file
    from pmc_turbo.ground.short_status_format import format_short_status_camera, get_item_name
    from collections import OrderedDict
    import time
    import glob
    import pandas as pd
    index_files = glob.glob('/data/piggyback_gse_data/*/openport/file_index.csv')
    index_files.sort()
    latest_index = index_files[-1]
    index_df = pd.read_csv(latest_index)
    leader_index = index_df[(index_df.file_type == 9) & (index_df.camera_id==254)]
    camera_index = index_df[(index_df.file_type == 9) & (index_df.camera_id!=254)]
    try:
        camera_ss = load_and_decode_file(camera_index.filename.iloc[-1]).short_status.values
    except Exception as e:
        raise e
        camera_ss = {}

    try:
        leader_ss = load_and_decode_file(leader_index.filename.iloc[-1]).short_status.values
    except Exception as e:
        raise e
        leader_ss = {}

    leader_items = ['timestamp',
                    'status_byte_camera_4',
                    'packets_queued_openport',
                    'current_file_id',
                    'highest_command_sequence',
                    'last_command_sequence',
                    'last_failed_sequence',
                    'last_outstanding_sequence',
                    'total_commands_received',
                    'bytes_per_sec_openport',
                    'bytes_sent_openport',
                    ]
    system = ['timestamp', 'uptime', 'load', 'watchdog_status',
       'downlink_queue_depth', 'free_disk_root_mb',
       'free_disk_var_mb', 'free_disk_data_1_mb', 'free_disk_data_2_mb',
       'free_disk_data_3_mb', 'free_disk_data_4_mb', 'free_disk_data_5_mb',
       'root_raid_status', 'var_raid_status',]
    camera = ['exposure_us', 'focus_step','aperture_times_100','trigger_interval', 'frame_rate_times_1000', 'frames_per_burst',
              'total_images_captured', 'camera_packet_resent', 'camera_packet_missed', 'camera_frames_dropped',
              'camera_timestamp_offset_us',]
    sensors = ['rail_12_mv',
       'pressure', 'lens_wall_temp', 'dcdc_wall_temp', 'labjack_temp',
       'camera_temp', 'ccd_temp',  'cpu_temp', 'sda_temp',
       'sdb_temp', 'sdc_temp', 'sdd_temp', 'sde_temp', 'sdf_temp',
       'sdg_temp', ]
    auto_exposure = ['auto_exposure_enabled', 'max_percentile_threshold',
       'min_peak_threshold', 'min_percentile_threshold',
       'adjustment_step_size', 'min_auto_exposure', 'max_auto_exposure',]
    tables = []
    for title,items in [('system',system),('sensors',sensors),('camera',camera),('auto_exposure',auto_exposure),('leader',leader_items)]:
        rows = [TR(TH(title))]
        for item in items:
            try:
                value, format = format_short_status_camera(item,camera_ss[item])
                name = get_item_name(item)
            except Exception:
                value = leader_ss[item]
                format = ''
                name = item
            if format == 'r':
                value = TD(value,_id="bad_value")
            elif format == 'b':
                value = TD(value,_id="cold")
            else:
                value = TD(value,_id="value")
            rows.append(TR(TD(TABLE(TR(TD(name),value),_id="sub_table"))))
        tables.append((title,TABLE(*rows)))

    messages = []
    camera_timestamp_age = time.time()-camera_ss['timestamp']
    if camera_timestamp_age > 600:
        messages.append("Camera status is old!")
    elif camera_timestamp_age < 30:
        messages.append("New camera status!")
    leader_timestamp_age = time.time() - leader_ss['timestamp']
    if leader_timestamp_age > 600:
        messages.append("Leader status is old!")
    elif leader_timestamp_age < 30:
        messages.append("New leaer status!")
    messages = ' -- '.join(messages)

    result =  dict(tables)
    response.flash = messages
    return result


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
<?php

/* Pass in by reference! */
function graph_aniwar_report ( &$rrdtool_graph ) {

    global $context,
           $hostname,
           $range,
           $rrd_dir,
           $size,
           $strip_domainname;

    if ($strip_domainname) {
       $hostname = strip_domainname($hostname);
    }

    $title = 'Aniwar Sessions';
    if ($context != 'host') {
       $rrdtool_graph['title'] = $title;
    } else {
       $rrdtool_graph['title'] = "$hostname $title last $range";
    }
    $rrdtool_graph['lower-limit']    = '0';
    $rrdtool_graph['vertical-label'] = 'Number';
    $rrdtool_graph['extras']         = '--rigid';
    $rrdtool_graph['height'] += ($size == 'medium') ? 28 : 0;

	$series = "DEF:'total'='${rrd_dir}/aniwar_total_sessions.rrd':'sum':AVERAGE "
		."DEF:'idle'='${rrd_dir}/aniwar_idle_sessions.rrd':'sum':AVERAGE "
		."DEF:'playback'='${rrd_dir}/aniwar_playback_sessions.rrd':'sum':AVERAGE "
		."DEF:'arena'='${rrd_dir}/aniwar_arena_sessions.rrd':'sum':AVERAGE "
		."AREA:'total'#3333bb:'Total Sessions' "
		."LINE1:'idle'#ffea00:'Idle Sessions' "
		."LINE2:'playback'#dd0000:'Playback Sessions' "
		."LINE1:'arena'#ff8a60:'Arena Sessions' "
	;

    $rrdtool_graph['series'] = $series;

    return $rrdtool_graph;

}

?>

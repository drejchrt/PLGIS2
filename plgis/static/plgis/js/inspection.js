var marking_allowed = false;

var first_corner;
var rect;

var $canvas = $('#canvas svg')

var markings = [];
var sightings = [];

function makeSVG(tag, attrs) {
    var el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (var k in attrs)
        el.setAttribute(k, attrs[k]);
    return el;
}

function construct_rectangle(p1, p3) {
    var w = p3[0] - p1[0];
    var h = p3[1] - p1[1];

    var p2 = [p1[0] + w, p1[1]];
    var p4 = [p1[0], p1[1] + h];

    var svg = makeSVG('polygon', {
        'points': `${p1} ${p2} ${p3} ${p4}`
    })
    $(svg).on('click', function () {
        $(svg).toggleClass('selected')
    });
    return $(svg)
}

function toggle_marking() {
    marking_allowed = !marking_allowed;
    if (marking_allowed) {
        $canvas.css('cursor', 'crosshair');
        $canvas.click(function (e) {
            var x = e.pageX - $(this).position().left;
            var y = e.pageY - $(this).position().top;

            // first click
            if (!first_corner) {
                first_corner = [x, y]
                // create rectangle
                rect = construct_rectangle(first_corner, [x + 1, y + 1])
                // activate resizing of the rectangle on mouse move
                $canvas.on('mousemove', function (me) {
                    var xx = me.pageX - $(this).position().left;
                    var yy = me.pageY - $(this).position().top;
                    rect.remove()
                    rect = construct_rectangle(first_corner, [xx, yy]).appendTo($canvas);
                })
            } //second click
            else {
                // fixate rectangle
                rect.remove()
                rect = construct_rectangle(first_corner, [x, y]).appendTo($canvas);
                // deactivate resizing
                $canvas.off('mousemove');
                // reset states
                first_corner = null;
                // popup mark form
                $('#new-mark-modal').modal('toggle')
            }
        })
    } else {
        $canvas.css('cursor', 'default');
        $canvas.off('click')
    }
}

function add_new_marking_to_list(mark) {
    // function that shows the new marking in tab and redraws the rectangle
    markings.push(mark);
    $(`<li>${mark.component}-${mark.type}-[${mark.severity}]</li>`).appendTo($('ul#new-marks-list'))
    $(makeSVG('polygon', {'points': mark.marking})).on('click', function () {
        $(this).toggleClass('selected')
    }).appendTo($canvas)
}

function add_new_sighting_to_list(mark) {
    sightings.push(mark)
    $(`<li>New sighting of fault :${mark.fault}</li>`).appendTo($('ul#new-marks-list'))
    $(makeSVG('polygon', {'points': mark.marking, id: mark.fault})).on('click', function () {
        $(this).toggleClass('selected')
    }).appendTo($canvas)
}

function translate_polygon_points(pts,tx,ty){
    var pts = pts.split(" ");
    var ans = ""
    for (var pt of pts){
        var x,y;
        [x, y] = pt.split(',');
        ans += `${parseInt(x)-tx},${parseInt(y)-ty} `;
    }
    return ans
}

$(document).ready(function () {
    $('button#marker-mode-button').click(function () {
        $(this).toggleClass('btn-outline-warning');
        $(this).toggleClass('btn-warning');

        toggle_marking()
    });

    // Handle dismiss modal to remove canceled marking
    $('#new-mark-modal').on('hide.bs.modal', function () {
        $(rect).remove()
    });

    $('#new-mark-modal-save').click(function () {
        //get active class in order to find out, which form should be checked
        if ($('ul.nav-tabs a.active').attr('href') == "#old") {
            var fault_id = $('input[name=mark_select]:checked').val()
            if (fault_id == 'other') {
                fault_id = $('select#all-marks').val()
            }
            var tpoints = translate_polygon_points(rect.attr('points'), t_x,t_y)
            var new_marking = {
                fault: fault_id,
                marking: tpoints
            }
            add_new_sighting_to_list(new_marking);
            $('#new-mark-modal').modal('hide');
        } else {
            var form = $('form#brand-new-marking-form');
            var tpoints = translate_polygon_points(rect.attr('points'), t_x,t_y)
            var new_marking = {
                'image': form.find('input#image').val(),
                // 'marking': rect.attr('points'),
                'marking': tpoints,
                'address': {
                    'circuit': form.find('input#circuit').val(),
                    'section': form.find('input#section').val(),
                    'traverse': form.find('select#traverse').val(),
                    'side': form.find('select#side').val(),
                    'bundle': form.find('select#bundle').val(),
                    'cable': form.find('select#cable').val(),
                },
                'component': form.find('select#mark_component').val(),
                'type': form.find('select#mark_type').val(),
                'severity': form.find('select#mark-severity-grade').val(),
                'comment': form.find('textarea#mark-comment').val(),

            }
            // TODO: Validate new marking
            add_new_marking_to_list(new_marking);
            put_new_markings_on_map()
            $('#new-mark-modal').modal('hide');
        }

    });

    // add new mark type from the text input into the options of the neighboring select
    $('#new-mark-modal button#add-new-mark-type').click(function () {
        var val = $('#new-mark-modal input#new-mark-type').val();
        $(`<option value="${val}">${val}</option>`)
            .appendTo($('#new-mark-modal select#mark_type'));
    });
    // add new component from the text input into the options of the neighboring select
    $('#new-mark-modal button#add-new-mark-component').click(function () {
        var val = $('#new-mark-modal input#new-mark-component').val();
        $(`<option value="${val}">${val}</option>`)
            .appendTo($('#new-mark-modal select#mark_component'));
    });

    // The map does not render due to some complex timing issues. This is a workaround
    $('#map-tab').click(function () {
        setTimeout(function () {
            map.updateSize();
        }, 1000);
    });

    // This handler updates the link to the selected marking on the opener button besides the select
    $('select#all-marks-select').on('input', function () {
        var href = $(this).find(`option[value=${$(this).val()}]`).attr('data-href');
        $('a#option-opener').attr('href', href);
    });

    // Show a confirmation modal, if there are some unsaved markings
    $('.hover-panel a').click(function (e) {
        if (markings.length != 0 || sightings.length != 0) {
            e.preventDefault()
            console.log($(this));
            $('#are-you-sure-modal a#confirm').attr('href', $(this).attr('href'));
            $('#are-you-sure-modal').modal('toggle')
        }
    });

    // Reset view
    $('button#reset-view-button').click(function(){
        t_x = 0;
        t_y = 0;
        $canvas.children().each(function(){
            $(this).attr('transform','translate(0,0)');
        })
    })

    $canvas.find('image').on('dragstart', function (e) {
        e.preventDefault();
    })

    // Make SVG element scrollable
    var t_x = 0;
    var t_y = 0;
    $canvas.mousedown(function (emd) {
        var md = [emd.clientX, emd.clientY];
        $canvas.mousemove(function (emm) {
            var vec = [emm.clientX - md[0], emm.clientY - md[1]]
            $canvas.children().each(function () {
                var x = vec[0]+t_x;
                var y = vec[1]+t_y;
                $(this).attr('transform', `translate(${x},${y})`);
            })

        })
    })
    $canvas.mouseup(function () {
        $canvas.off('mousemove');
        var ts = $canvas.find('image').attr('transform').match(/-?\d+/g);
        t_x = parseInt(ts[0]);
        t_y = parseInt(ts[1]);
    })

});

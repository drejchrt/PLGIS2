function selector_activate_options() {

    $(".selector").each(function () {
        var selector = $(this);
        selector.find("option").each(function(){
            $(this).off('dblclick');
            $(this).dblclick(function(){
               var current_select = $(this).parent().attr('id');
               var destination_select = (current_select == 'available') ? '#selected' : '#available';
               $(this).appendTo(selector.find(destination_select));
            });
        });
    });

}

function add_option(option,selector) {
            var new_comp_name = option;
            $("<option value=\"" + new_comp_name + "\">" + new_comp_name + "</option>")
                .appendTo(selector.find("select#available"));
            selector_activate_options()
        }
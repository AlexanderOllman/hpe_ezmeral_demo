// Javascript file for managing TEITS editor


$('#main_map.drop').droppable({
    drop : function(e,ui){
        console.log("main map drop");
        var zone_id = ui.draggable.attr('id');
        var top = ui.draggable.offset().top / ui.draggable.parent().height() * 100;
        var left = ui.draggable.offset().left / ui.draggable.parent().width() * 100;
        console.log(top);
        console.log(left);
        set_zone_position(zone_id,top,left); 
    },
}); 

function save_zone(){
    if ($("#zone_name").val()!=""){
    console.log("Saving zone : " + $("#zone_name").val())
    $.ajax({
            url: 'save_zone',
            type: 'post',
            data: {"zone_name":$("#zone_name").val(),
                    "zone_width":$("#zone_width").val(),
                    "zone_height":$("#zone_height").val(),
                    "zone_top":$("#zone_top").val(),
                    "zone_left":$("#zone_left").val(),
                    "zone_x":$("#zone_x").val(),
                    "zone_y":$("#zone_y").val(),
                    },
            success:function(data){
                location.reload();
            }
        });
    }
}

$("#zone_save").click(function(){
        save_zone();
})


$("#zone_delete").click(function(){
        $.ajax({
            url: 'delete_zone',
            type: 'post',
            data: {"zone_name":$("#zone_name").val()
                    },
            success:function(data){
                console.log(data);
                location.reload();
            }
        });
})


function update_zone_info(zone_id){
    var zone_div = $("#"+zone_id);
    $("#zone_name").val(zone_div.attr("id"));
    $("#zone_height").val(Math.round(zone_div.height()/zone_div.parent().height()*100));
    $("#zone_width").val(Math.round(zone_div.width()/zone_div.parent().width()*100));
    $("#zone_top").val(Math.round(zone_div.offset().top/zone_div.parent().height()*100));
    $("#zone_left").val(Math.round(zone_div.offset().left/zone_div.parent().width()*100));
}

$(".zone.drag").click(function(){
    console.log("update");
    var zone_id = $(this).attr("id")
    update_zone_info(zone_id);
    update_zone_coordinates(zone_id);
})


function update_zone_coordinates(zone_id){
    console.log("get coord");
    $.ajax({
            url: 'get_zone_coordinates',
            type: 'post',
            data: {"zone_id":zone_id},
            success:function(data){
                coordinates = JSON.parse(data);
                console.log(coordinates)
                $("#zone_x").val(coordinates.x);
                $("#zone_y").val(coordinates.y);
            }
        });
}

function set_zone_position(zone_id,top,left){
    console.log("set position");
    $.ajax({
            url: 'set_zone_position',
            type: 'post',
            data: {"zone_id":zone_id,"top":top,"left":left},
            success:function(data){
                console.log("position: ");
                console.log(data);
            }
        });
}


$(function(){
    $('.drag').draggable({revert:"invalid",revertDuration: 300}); // appel du plugin
});

function AvoidSpace(event) {
    var k = event ? event.which : window.event.keyCode;
    if (k == 32) return false;
}

function NumbersOnly(event) {
    var k = event ? event.which : window.event.keyCode;
    if (k < 45 || k > 57 || k == 47) return false;
}
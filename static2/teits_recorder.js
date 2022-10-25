// Javascript file for managing TEITS recorder

var current_timer = 0;
var timer

function tick(){
    console.log(current_timer);
    $("#minutes").html(Math.trunc(current_timer/600)%60);
    $("#seconds").html(Math.trunc(current_timer/10)%60);
    $("#tenths").html(current_timer%10);
    current_timer = current_timer + 1;
}





$('#recorder_btn').click(function(){
    var button = $(this);
    if(button.text()=="START"){
        button.html("Starting ...");
        $.ajax({
            url: 'start_recording',
            type: 'post',
            data: {"zone_name":$("#zone_selector").val()
                    },
            success:function(data){
                button.html("STOP");
                $("#status").html("Recording ...");
                timer_on= true;
                timer = setInterval(function(){tick();},100)
            }
        });

    }else{
        $.ajax({
            url: 'stop_recording',
            type: 'post',
            success:function(data){
                button.html("START");
                $("#status").html("");
                clearInterval(timer);
                current_timer = 0;
            }
        });
    }
}); 

$('#delete_btn').click(function(){
    $("#status").html("Deleted");
    $.ajax({
        url: 'delete_recording',
        type: 'post',
        data: {"zone_name":$("#zone_selector").val()
                },
        success:function(data){
            $("#recorder_btn").text("START");
            $("#status").html("Deleted");
            clearInterval(timer);
            setTimeout(function(){
                $("#status").html("");
            },3000);
        }
    });
}); 




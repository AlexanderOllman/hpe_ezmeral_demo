var selector_cities = []
var cities = [];
var count=true;
var title_desc = "count"
var consolidate = true;
var updating_charts = true;
var update_chart_timer = 2;
var update_streams_timer = 5;
var update_counter_timer = 1;

function contains(array,string){
    var in_array = false; 
    for (var i=0;i<array.length;i++){
        if (array[i]==string){
            in_array = true;
            break;
        }
    }
    return in_array;
}



function create_charts(){
    if (consolidate){
        if (!$("#Global").length){create_chart("Global");}
    }else{
        for (var i=0;i<cities.length;i++){
            var city = cities[i];
            if (!$("#"+city).length){
                console.log("creating chart for " + city);
                create_chart(city);
            }
        }
    }
}

function create_chart(city){
    if (!$('#'+city).length){
        $('#charts').append("<div class='col-md-6' id="+city+"></div>");
    }
    var myChart = Highcharts.chart(city, {
        chart: {
            type: 'column'
        },
        title: {
            text: city + " " + title_desc
        },
        xAxis: {
            categories: []
        },
        yAxis: {
            title: {
                text: 'Count'
            }
        },
        series: [{
            data: []
        }]
    });
    return myChart;
}




function update_charts(){
    updating_charts = false;
    // console.log("update charts for " + cities + "(consolidate = "+consolidate+")");
    // Create missing charts if needed
    create_charts();
    $.ajax({
        url: 'get_stream_data',
        type: 'post',
        data:{"cities":JSON.stringify(cities),"consolidate":consolidate,"count":count},
        success:function(data){
            loaded_data = JSON.parse(data);

            // Iterate over object
            $.each(loaded_data,function(key,value){
                // get chart
                if (key == "Global" || contains(cities,key)){
                    var chart=$("#"+key).highcharts();
                    var new_data = [];
                    var categories = [];
                    // get and update values
                    if (chart){
                        var chart_data = chart.series[0].data;

                        for (var i = 0; i < chart_data.length; i++) {
                            category = chart_data[i].category;
                            categories.push(category);
                            current_value = chart_data[i].y;
                            incoming_value = value[category];
                            if (incoming_value){
                                new_value = current_value + incoming_value;
                            }else{
                                new_value = current_value;
                            }
                            new_data.push(new_value);
                            delete value[category];
                        }
                        for (var category in value){
                            if ((category != "count" && (count || category == "gkm")) || category != "count" && category != "gkm"){
                                categories.push(category);
                                new_data.push(value[category]);                        
                            }
                        }
                        chart.xAxis[0].setCategories(categories);
                        chart.series[0].setData(new_data);
                    }
                }
            })
            
            updating_charts = true;
            setTimeout(function(){
                update_charts();
              }, 1000 * update_chart_timer);
        }
    });
}




function update_stream_selector(){
    $.ajax({
        url: 'get_all_streams',
        type: 'get',
        success:function(data){
            var available_cities = JSON.parse(data);
            for (var i=0;i<available_cities.length;i++){
                var city = available_cities[i];
                if (! contains(selector_cities,city)){
                    if ($("#all_streams").is(':checked')){ checked = 'checked="checked"'}else{checked=""}                    
                    $("#stream_selector").append($( "<span id='" + city + "_selector'><input class='city' type='checkbox' data-city='" + city + 
                        "' name='stream' value='city' "+ checked + " > " + city + "</span><p>"));
                    selector_cities.push(city);
                    if (checked){cities.push(city);}
                }
            }
            for (var i=0;i<cities.length;i++){
                var city = cities[i];
                if (! contains(available_cities,city)){
                    $("#" + city + "_selector").remove();
                    $("#" + city).remove();
                    var index = cities.indexOf(city);
                    if (index > -1) {
                        cities.splice(index, 1);
                    }
                }
            }
            setTimeout(function(){
                update_stream_selector();
              }, 1000 * update_streams_timer);
        }
    });
}



function update_events(){
    $.ajax({
        url: 'get_events_count',
        type: 'get',
        success:function(data){
            var current_count = $("#event_count").data("count");
            new_count = JSON.parse(data).count;
            console.log("new count : " + new_count);
            if (new_count != current_count){
                $("#event_count").data("count",new_count);
                $("#event_count").prop('Counter',current_count).animate(
                    {
                        Counter: new_count
                    },
                    {
                        duration: update_counter_timer * 1000,
                        easing: 'linear',
                        step: function (now) {
                            $(this).text(Math.ceil(now));
                        }
                    });
                setTimeout(function(){
                    update_events();
                  }, 1000 * update_counter_timer);
            }else{
            update_events();
            }
        }
    });
}


$("#deploy_new_country_btn").click(function(){
  var new_country = $("#new_country").val();
  console.log("deploying new country : " + new_country);
  $("#deploy_new_country_btn").text("Deploying ...");
  $.ajax({
      url: 'deploy_new_country',
      type: 'post',
      data: {"country":new_country},
      success:function(data){
          get_countries();
          $("#new_country").val("");
          $("#deploy_new_country_btn").text("Deploy");
      }
  });
})


function get_countries(){
    $.ajax({
        url: 'get_countries',
        type: 'get',
        success:function(data){
            var countries = JSON.parse(data)["countries"];
            $("#countries").html("");
            for(var i=0;i<countries.length;i++){
                $("#countries").append("<div class='row'><div class='col-md-9'><a href=http://global:" + countries[i].port + " target='_blank'>" + countries[i]._id + "</a></div>" +
                                       "<div class='col-md-3'><a href='#' data-country='" + countries[i]._id + "' class='remove_country text-danger float-right' > x</a></div></div>");
            }
        }
    });
}


$("#countries").on('click',".remove_country",function(){
  var country = $(this).data('country');
  console.log("removing country : " + country);
  $.ajax({
      url: 'remove_country',
      type: 'post',
      data: {"country":country},
      success:function(data){
          get_countries();
      }
  });
})


$(".radio-inline").change(function(){
  count = $("#count_radio").is(':checked');
  if (count){title_desc = "count"}else{title_desc = "emissions"}
  consolidate = $("#consolidate_radio").is(':checked');
  $("#charts").empty();
  create_charts()
});

$("#stream_selector").change(function(e){
  cities = []
  if(e.target.id == "all_streams"){
    if (e.target.checked){
      $('#stream_selector :input').prop('checked', true);  
    }else{
      $('#stream_selector :input').prop('checked', false); 
    }
  }else{
    if (! e.target.checked){
      $('#all_streams').prop('checked', false); 
    }
  }

  $(".city").each(function(){
      if(this.checked == true){
          console.log(this);
          input_city = $(this).data("city")
          if (input_city != "all"){
            cities.push(input_city);
          }
      }
  });

  $("#charts").empty();
  create_charts();
  if (!updating_charts){
    update_charts();
  }

});


$("#replicate_streams").click(function(){
    $("#replicate_streams").text("Replicating ...");
    $.ajax({
        url: 'replicate_streams',
        type: 'get',
        success:function(data){
            setTimeout(function(){
              $("#replicate_streams").text("Replicate streams");
            }, 1000 * 10);
          }
    });
});

$( document ).ready(function() {;
  console.log("ready")
  update_stream_selector();
  update_charts();
  update_events();
  get_countries();
});

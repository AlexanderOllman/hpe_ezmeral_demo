var cities = [];


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

function update_cities(){
    console.log("update_cities");   
    $.ajax({
        url: 'get_all_streams',
        type: 'get',
        success:function(data){
            var new_cities = JSON.parse(data);
            for (var i=0;i<cities.length;i++){
                city = cities[i];
                if (!contains(new_cities,city)){
                    console.log("removing chart for " + city);
                    $("#"+city).remove();
                }
            }
            cities = new_cities;
            setTimeout(function(){
                update_cities();
              }, 1000 * 5);
        }
    });
}



function create_chart(city){
    console.log("creating chart for " + city);
    if (!$('#'+city).length){
        $('#charts').append("<div class='col-md-4' id="+city+"></div>");

    }
    var myChart = Highcharts.chart(city, {
        chart: {
            type: 'column'
        },
        title: {
            text: city
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
            showInLegend: false, 
            data: []
        }]
    });
    return myChart;

}



function update_charts(){
    console.log("update charts");
    $.ajax({
        url: 'get_stream_data',
        type: 'post',
        data:{"cities":JSON.stringify(cities),"consolidate":false,"count":true},
        success:function(data){
            loaded_data = JSON.parse(data);
            // Iterate over object
            $.each(loaded_data,function(key,value){
                // get or create chart
                if (!$('#'+key).length){
                    create_chart(key);
                }
                var chart=$("#"+key).highcharts();
                // get and update values
                var chart_data = chart.series[0].data;
                //console.log(chart_data);
                var new_data = [];
                var categories = [];
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
                    if (category != "count"){
                        categories.push(category);
                        new_data.push(value[category]);                        
                    }
                }
                chart.xAxis[0].setCategories(categories);
                chart.series[0].setData(new_data);  
            })
            
            setTimeout(function(){
                update_charts();
              }, 1000 * 2);
        }
    });
}


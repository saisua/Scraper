function main(){
    let frame = document.createElement("div");
    frame.id = "overmenu";

    let nodes = [
        ["div", {
            id : "\"overmenu_header\"",
			innerText : "\"drag to move\""
        }],
        ["div", {
            id : "\"overmenu_minimize\"",
            innerText : "\"^\""
        }],
        ["div", {
            id : "\"options\""
        }],
        ["div", {
            id : "\"overmenu_resize\"", 
            innerText : "\"#\""
        }],
    ];

    for(node of nodes){
        let new_node = document.createElement(node[0]);
        
        let attributes = node[1];
        for(let attribute in attributes){
			eval("new_node."+attribute+"="+attributes[attribute]);
        }

		frame.appendChild(new_node);		
    }

    // console.log(frame);
	document.body.appendChild(frame);
	
	frame.style.left = window.innerWidth-175-15+"px";
	frame.style.top = window.innerHeight-200+"px";
}

main();

var over_menu = document.getElementById("overmenu");
elementAllowMove(over_menu);
elementAllowResize(over_menu);
elementOnMouseOver(over_menu);

var minimize = document.getElementById("overmenu_minimize");
var options = document.querySelector("div[id='overmenu'] div[id='options']");
var resize = document.getElementById("overmenu_resize");
elementMinimize(minimize, options, resize, over_menu);



function elementAllowMove(element) {
	var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
	if (document.getElementById(element.id + "_header")) {
		/* if present, the header is where you move the DIV from:*/
		document.getElementById(element.id+"_header").onmousedown = dragMouseDown;
	} else {
		document.getElementById(element.id).onmousedown = dragMouseDown;
	}


	function dragMouseDown(e) {
		e = e || window.event;
		e.preventDefault();
		// get the mouse cursor position at startup:
		pos3 = e.clientX;
		pos4 = e.clientY;
		document.onmouseup = closeDragElement;
		// call a function whenever the cursor moves:
		document.onmousemove = elementDragMove;
	}

	function elementDragMove(e) {
		e = e || window.event;
		e.preventDefault();
		// calculate the new cursor position:
		pos1 = pos3 - e.clientX;
		pos2 = pos4 - e.clientY;
		pos3 = e.clientX;
		pos4 = e.clientY;
        // set the element's new position:
        
        let new_top = (element.offsetTop - pos2);
        let new_left = (element.offsetLeft - pos1);

        if(new_top > 0)
		    element.style.top = new_top + "px";
        if(new_left > 0)
            element.style.left = new_left + "px";
	}
	
	function closeDragElement() {
		/* stop moving when mouse button is released:*/
		document.onmouseup = null;
		document.onmousemove = null;
	}
}

function elementAllowResize(element) {
	var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
	if (document.getElementById(element.id + "_resize")) {
		/* if present, the header is where you move the DIV from:*/
		document.getElementById(element.id+"_resize").onmousedown = resizeMouseDown;
	} else {
		document.getElementById(element.id).onmousedown = resizeMouseDown;
	}
	
	function resizeMouseDown(e) {
		e = e || window.event;
		e.preventDefault();
		// get the mouse cursor position at startup:
		pos3 = e.clientX;
		pos4 = e.clientY;
		document.onmouseup = closeDragElement;
		// call a function whenever the cursor moves:
		document.onmousemove = elementDragResize;
	}
	
	function elementDragResize(e) {
		e = e || window.event;
		e.preventDefault();
		// calculate the new cursor position:
		pos1 = pos3 - e.clientX;
		pos2 = pos4 - e.clientY;
		
		console.log(element.style.width - pos1);
		
		pos3 = e.clientX;
		pos4 = e.clientY;
		// set the element's new position:
		element.style.height = (element.offsetHeight - pos2) + "px";
		element.style.width = (element.offsetWidth - pos1) + "px";
	}

	function closeDragElement() {
		/* stop moving when mouse button is released:*/
		document.onmouseup = null;
		document.onmousemove = null;
	}
}

function elementOnMouseOver(element){
	element.onmouseover = over_opac;
	element.onmouseout = out_dim;

	var dim_timeout = false;
	var anim_direction = 1;
	var anim_speed = 1;


	var is_over = false;

	function over_opac(e){
		e = e || window.event;
		e.preventDefault();

		// Opacity visual		
		if(dim_timeout){
			clearInterval(dim_timeout);
			dim_timeout = false;
		}

		element.style.opacity = 1;	
	}

	function out_dim(e){
		e = e || window.event;
		e.preventDefault();
		
		dim_timeout = setTimeout(() => {
			element.style.opacity = 0.5;
			dim_timeout = false;
			},
			1500);	
	}
}

var menu_animation = [{
		opacity: 0,
		transform: "scale(0)"
	},{
		transform: "scale(1.07)",
		offset: 0.8
	},{
		opacity: 1,
		transform: "scale(1)"
	}];

var menu_div_animation = [{
		opacity: 0,
		transform: "scaleY(0)"
	},{
		opacity: 1,
		transform: "scaleY(1)"
	}];

var pre_height = 200;
var reverse = false;
function elementMinimize(button, element, resize, over_menu){
	button.onclick = switch_minimize;

	function switch_minimize() {
		reverse = !reverse;
		for(let child_num = 0; child_num < element.childNodes.length; child_num++)
			setTimeout(()=>{
				element.childNodes[child_num].animate(menu_animation, 
					{
						duration:600, 
						direction:(reverse ? "reverse" : "normal")
					});
				element.childNodes[child_num].style.opacity = (reverse ? 0 : 1);
			}, 60*child_num);

        button.innerText = (reverse ? "v" : "^");
            
		resize.style.opacity = (reverse ? 0 : 1);

		element.animate(menu_div_animation, 
			{
				duration:600 + 60*(element.childNodes.length-1), 
				direction:(reverse ? "reverse" : "normal")
			});



		if(reverse){
			pre_height = element.offsetHeight;
			element.style.height = 0;
		} else {
			element.style.height = pre_height-2+"px";
		}


		over_menu.animate([
			{transform:"translate(0,"+pre_height+"px)"},
			{transform:"translate(0,0)"}
		],{
			duration:300, 
			delay:(reverse ? (600 + 60*(element.childNodes.length-1)) : 0),
			direction:(reverse ? "reverse" : "normal")
		});

		setTimeout(()=>
			(over_menu.style.top = over_menu.offsetTop + (reverse ? pre_height : -pre_height) + "px"),
				(reverse ? (900 + 60*(element.childNodes.length-1)) : 0));

	}
}

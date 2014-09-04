$(document).ready(function(){
	$(window).blur(function(){
		var game_id = $("#game_id").val();
		vex.dialog.open({
			message: "Oh, we went to another tab, did we? <br> Maybe went to rottentomatoes.com? <br> NO ROUND FOR YOU.",
			buttons: [
				$.extend({}, vex.dialog.buttons.YES, {
      				text: 'Start new round'})
			]

		});
	});


});
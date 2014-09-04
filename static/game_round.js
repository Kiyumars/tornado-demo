$(document).ready(function(){
	var cheat_activated = false;
	$(window).blur(function(){
		if (cheat_activated == false){
			var game = $("#game_id").val();
			cheat_activated = true;
			vex.dialog.open({
				message: "Oh, we went to another tab, did we? <br> Maybe we went to rottentomatoes.com, hmmm? <br> THIS ROUND IS CLOSED!<br>NO POINTS FOR ANYONE!",
				overlayClosesOnClick: false,
				buttons: [
					$.extend({}, vex.dialog.buttons.YES, {
	      				text: 'Start new round'})
				],
				callback: function(){
					
						window.location.href = "/next_round?game_id=" + game; 
					
				}

			});
		}
	});


});
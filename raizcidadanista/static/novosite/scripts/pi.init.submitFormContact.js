/* Aura version: 1.8.7 */

jQuery(function($){
	"use strict";

	//region Init Footer Form submit
	$('.pi-contact-form').submit(function(){

		var $form = $(this),
			$error = $form.find('.pi-error-container'),
			action  = $form.attr('action');

		$error.slideUp(750, function() {
			$error.hide();

			var $name = $form.find('.form-control-name'),
				$email = $form.find('.form-control-email'),
				$companyName = $form.find('.form-control-company-name'),
				$phone = $form.find('.form-control-phone'),
				$budjet = $form.find('.form-control-budjet'),
				$comments = $form.find('.form-control-comments'),
				$captcha = $form.find('.g-recaptcha'),
				$captchaResponse = $form.find('[name="g-recaptcha-response"]');

			$.post(action, {
					name: $name.val(),
					email: $email.val(),
					companyName: $companyName.val(),
					phone: $phone.val(),
					budjet: $budjet.val(),
					comments: $comments.val(),
					captcha_enabled: $captcha.length > 0 ? 1 : 0,
					captcha_response: $captchaResponse.length > 0 ? $captchaResponse.val() : 0
				},
				function(data){
					$error.html(data);
					$error.slideDown('slow');

					if (data.match('success') !== null) {
						$name.val('');
						$email.val('');
						$companyName.val('');
						$phone.val('');
						$budjet.val('');
						$comments.val('');
					}
				}
			);

		});

		return false;

	});
	//endregion

});
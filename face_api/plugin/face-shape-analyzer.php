<?php
/**
 * Plugin Name: Face Shape Analyzer
 * Plugin URI: https://example.com/
 * Description: Upload a portrait, send it to an external face analysis API, and display polished visual insights through a shortcode.
 * Version: 1.0.3
 * Author: Codex
 * Text Domain: face-shape-analyzer
 */

if (! defined('ABSPATH')) {
	exit;
}

final class FSA_Face_Shape_Analyzer {
	private const OPTION_NAME = 'fsa_face_shape_analyzer_settings';
	private const NONCE_ACTION = 'fsa_process_face_analysis';
	private const AJAX_ACTION = 'fsa_process_face_analysis';
	private const VERSION = '1.0.3';
	private const SHORTCODE = 'face_shape_analyzer';

	public function __construct() {
		add_action('admin_menu', array($this, 'register_admin_page'));
		add_action('admin_init', array($this, 'register_settings'));
		add_action('wp_enqueue_scripts', array($this, 'register_assets'));
		add_shortcode(self::SHORTCODE, array($this, 'render_shortcode'));
		add_action('wp_ajax_' . self::AJAX_ACTION, array($this, 'handle_process_request'));
		add_action('wp_ajax_nopriv_' . self::AJAX_ACTION, array($this, 'handle_process_request'));
	}

	public function register_admin_page() {
		add_options_page(
			__('Face Shape Analyzer', 'face-shape-analyzer'),
			__('Face Shape Analyzer', 'face-shape-analyzer'),
			'manage_options',
			'face-shape-analyzer',
			array($this, 'render_settings_page')
		);
	}

	public function register_settings() {
		register_setting(
			self::OPTION_NAME,
			self::OPTION_NAME,
			array($this, 'sanitize_settings')
		);
	}

	public function register_assets() {
		$style_path = plugin_dir_path(__FILE__) . 'assets/css/face-shape-analyzer.css';
		$script_path = plugin_dir_path(__FILE__) . 'assets/js/face-shape-analyzer.js';

		wp_register_style(
			'fsa-google-fonts',
			'https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap',
			array(),
			null
		);

		wp_register_style(
			'fsa-face-shape-analyzer',
			plugin_dir_url(__FILE__) . 'assets/css/face-shape-analyzer.css',
			array('fsa-google-fonts'),
			file_exists($style_path) ? (string) filemtime($style_path) : self::VERSION
		);

		wp_register_script(
			'fsa-face-shape-analyzer',
			plugin_dir_url(__FILE__) . 'assets/js/face-shape-analyzer.js',
			array(),
			file_exists($script_path) ? (string) filemtime($script_path) : self::VERSION,
			true
		);
	}

	public function render_shortcode($atts = array(), $content = null) {
		wp_enqueue_style('fsa-face-shape-analyzer');
		wp_enqueue_script('fsa-face-shape-analyzer');

		$settings = $this->get_settings();
		$settings_url = current_user_can('manage_options')
			? admin_url('options-general.php?page=face-shape-analyzer')
			: '';

		static $localized = false;
		if (! $localized) {
			wp_localize_script(
				'fsa-face-shape-analyzer',
				'fsaFaceShapeAnalyzer',
				array(
					'ajaxUrl'         => admin_url('admin-ajax.php'),
					'nonce'           => wp_create_nonce(self::NONCE_ACTION),
					'action'          => self::AJAX_ACTION,
					'maxFileSizeMb'   => 8,
					'isConfigured'    => ! empty($settings['endpoint_url']),
					'canConfigure'    => current_user_can('manage_options'),
					'settingsUrl'     => $settings_url,
					'texts'           => array(
						'selectFile'       => __('Choose Portrait', 'face-shape-analyzer'),
						'analyze'          => __('Analyze Face', 'face-shape-analyzer'),
						'analyzing'        => __('Analyzing portrait...', 'face-shape-analyzer'),
						'uploadAnother'    => __('Analyze Another Face', 'face-shape-analyzer'),
						'dropPrompt'       => __('Drop a front-facing portrait', 'face-shape-analyzer'),
						'dropHint'         => __('Drag and drop your image here, or browse from your device.', 'face-shape-analyzer'),
						'dropReady'        => __('Portrait staged. Releasing into scan mode now...', 'face-shape-analyzer'),
						'scanningTitle'    => __('Scanning facial geometry', 'face-shape-analyzer'),
						'scanningHint'     => __('Reading symmetry, feature balance, and shape relationships.', 'face-shape-analyzer'),
						'chooseAnother'    => __('Choose Another Portrait', 'face-shape-analyzer'),
						'configMissing'    => __('The analyzer is not connected yet. Ask the site admin to configure the API settings.', 'face-shape-analyzer'),
						'genericError'     => __('Something went wrong while processing the portrait. Please try again.', 'face-shape-analyzer'),
						'unsupportedImage' => __('Please upload a JPG, PNG, or WEBP portrait.', 'face-shape-analyzer'),
						'maxFileSize'      => __('Please upload an image smaller than 8MB.', 'face-shape-analyzer'),
					),
				)
			);

			$localized = true;
		}

		$instance = 'fsa-' . wp_generate_password(8, false, false);
		$tabs = $this->get_tab_definitions();

		ob_start();
		?>
		<section class="fsa-widget" id="<?php echo esc_attr($instance); ?>" data-fsa-widget>
			<div class="fsa-shell">
				<input
					class="fsa-file-input"
					id="<?php echo esc_attr($instance); ?>-file"
					type="file"
					name="portrait"
					accept="image/jpeg,image/png,image/webp"
					data-fsa-file-input
				/>

				<div class="fsa-intake-shell" data-fsa-intake-shell>
					<div class="fsa-intake-card">
						<div class="fsa-intake-stage">
							<div class="fsa-intake-stage__frame">
								<div class="fsa-intake-stage__placeholder" data-fsa-drop-empty>
									<div class="fsa-stage-visual" aria-hidden="true">
										<div class="fsa-stage-visual__focus">
											<span></span><span></span><span></span><span></span>
										</div>
										<div class="fsa-stage-visual__beam"></div>
										<div class="fsa-stage-visual__portrait">
											<div class="fsa-stage-visual__head"></div>
											<div class="fsa-stage-visual__body"></div>
										</div>
										<div class="fsa-stage-visual__chips">
											<span><?php esc_html_e('Oval', 'face-shape-analyzer'); ?></span>
											<span><?php esc_html_e('Round', 'face-shape-analyzer'); ?></span>
											<span><?php esc_html_e('Square', 'face-shape-analyzer'); ?></span>
											<span><?php esc_html_e('Heart', 'face-shape-analyzer'); ?></span>
										</div>
									</div>
								</div>

								<div class="fsa-dropzone__preview is-hidden" data-fsa-drop-preview>
									<img class="fsa-intake-image" data-fsa-intake-image alt="<?php esc_attr_e('Selected portrait preview', 'face-shape-analyzer'); ?>" />
									<div class="fsa-scan-overlay is-hidden" data-fsa-scan-overlay>
										<div class="fsa-scan-overlay__grid"></div>
										<div class="fsa-scan-overlay__line"></div>
										<div class="fsa-scan-overlay__corners">
											<span></span><span></span><span></span><span></span>
										</div>
										<div class="fsa-scan-overlay__hud">
											<span><?php esc_html_e('Scanning Facial Geometry', 'face-shape-analyzer'); ?></span>
											<strong><?php esc_html_e('Reading symmetry, shape, and feature balance', 'face-shape-analyzer'); ?></strong>
										</div>
									</div>
								</div>
							</div>
						</div>

						<div class="fsa-intake-copy">
							<div
								class="fsa-dropzone"
								data-fsa-dropzone
								role="button"
								tabindex="0"
								aria-controls="<?php echo esc_attr($instance); ?>-file"
								aria-label="<?php esc_attr_e('Upload a face portrait', 'face-shape-analyzer'); ?>"
							>
								<div class="fsa-dropzone__inner">
									<div class="fsa-dropzone__icon" aria-hidden="true">
										<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">
											<path d="M12 4v10"></path>
											<path d="m7.5 8.5 4.5-4.5 4.5 4.5"></path>
											<path d="M5 15.5v1.8A1.7 1.7 0 0 0 6.7 19h10.6a1.7 1.7 0 0 0 1.7-1.7v-1.8"></path>
										</svg>
									</div>
									<h3 data-fsa-intake-title><?php esc_html_e('Upload Image', 'face-shape-analyzer'); ?></h3>
									<p data-fsa-intake-description><?php esc_html_e('JPG, PNG, or WEBP - Max 8MB', 'face-shape-analyzer'); ?></p>
									<div class="fsa-dropzone__meta">
										<span><?php esc_html_e('Drag and drop supported', 'face-shape-analyzer'); ?></span>
										<span><?php esc_html_e('Private 30 min links', 'face-shape-analyzer'); ?></span>
									</div>
									<span class="fsa-dropzone__button"><?php esc_html_e('Choose Image', 'face-shape-analyzer'); ?></span>
								</div>
							</div>

							<div class="fsa-status" aria-live="polite" data-fsa-status></div>

							<p class="fsa-helper-text"><?php esc_html_e('Use one clear, front-facing portrait for the best scan.', 'face-shape-analyzer'); ?></p>

							<?php if (! empty($settings_url) && empty($settings['endpoint_url'])) : ?>
								<div class="fsa-admin-hint">
									<p>
										<?php esc_html_e('API connection still needs to be configured.', 'face-shape-analyzer'); ?>
										<a href="<?php echo esc_url($settings_url); ?>"><?php esc_html_e('Open plugin settings', 'face-shape-analyzer'); ?></a>
									</p>
								</div>
							<?php endif; ?>
						</div>
					</div>
				</div>

				<div class="fsa-results-layout is-hidden" data-fsa-results-shell>
					<aside class="fsa-sidebar">
						<div class="fsa-card fsa-card--media">
							<div class="fsa-media-stage">
								<img class="fsa-preview-image" data-fsa-result-image alt="<?php esc_attr_e('Analyzed portrait preview', 'face-shape-analyzer'); ?>" />
								<div class="fsa-preview-badge">
									<span><?php esc_html_e('Analysis Complete', 'face-shape-analyzer'); ?></span>
								</div>
							</div>
						</div>

						<div class="fsa-card fsa-card--sidebar-meta">
							<div class="fsa-sidebar-copy">
								<span class="fsa-kicker"><?php esc_html_e('Studio Snapshot', 'face-shape-analyzer'); ?></span>
								<h3 class="fsa-sidebar-title"><?php esc_html_e('Results are ready', 'face-shape-analyzer'); ?></h3>
								<p class="fsa-sidebar-description"><?php esc_html_e('Feature ratings, quality signals, and recommendations from the live response appear below.', 'face-shape-analyzer'); ?></p>
							</div>

							<div class="fsa-quality-chips" data-fsa-quality></div>

							<div class="fsa-feature-ratings is-hidden" data-fsa-feature-ratings>
								<div class="fsa-section-heading">
									<h4><?php esc_html_e('Feature Ratings', 'face-shape-analyzer'); ?></h4>
								</div>
								<div class="fsa-feature-ratings__list" data-fsa-feature-ratings-list></div>
							</div>

							<div class="fsa-upload-actions">
								<button class="fsa-button fsa-button--ghost" type="button" data-fsa-reupload>
									<?php esc_html_e('Analyze Another Face', 'face-shape-analyzer'); ?>
								</button>
							</div>
						</div>
					</aside>

					<div class="fsa-main">
						<nav class="fsa-tabs" aria-label="<?php esc_attr_e('Face analysis sections', 'face-shape-analyzer'); ?>">
							<?php foreach ($tabs as $index => $tab) : ?>
								<button
									class="fsa-tab<?php echo 0 === $index ? ' is-active' : ''; ?>"
									type="button"
									data-tab="<?php echo esc_attr($tab['slug']); ?>"
									<?php echo 0 === $index ? 'aria-current="true"' : ''; ?>
								>
									<span class="fsa-tab__icon" aria-hidden="true"><?php echo $this->get_icon_markup($tab['slug']); ?></span>
									<span class="fsa-tab__label"><?php echo esc_html($tab['label']); ?></span>
								</button>
							<?php endforeach; ?>
						</nav>

						<div class="fsa-card fsa-card--results">
							<div data-fsa-results></div>
						</div>
					</div>
				</div>
			</div>
		</section>
		<?php

		return (string) ob_get_clean();
	}

	public function render_settings_page() {
		if (! current_user_can('manage_options')) {
			return;
		}

		$settings = $this->get_settings();
		?>
		<div class="wrap">
			<h1><?php esc_html_e('Face Shape Analyzer', 'face-shape-analyzer'); ?></h1>
			<p><?php esc_html_e('Configure the external API that receives portrait uploads and returns the facial analysis JSON.', 'face-shape-analyzer'); ?></p>

			<?php settings_errors(self::OPTION_NAME); ?>

			<form method="post" action="options.php">
				<?php settings_fields(self::OPTION_NAME); ?>

				<table class="form-table" role="presentation">
					<tbody>
						<tr>
							<th scope="row">
								<label for="fsa-endpoint-url"><?php esc_html_e('API endpoint URL', 'face-shape-analyzer'); ?></label>
							</th>
							<td>
								<input
									id="fsa-endpoint-url"
									class="regular-text code"
									type="url"
									name="<?php echo esc_attr(self::OPTION_NAME); ?>[endpoint_url]"
									value="<?php echo esc_attr($settings['endpoint_url']); ?>"
									placeholder="https://api.example.com/analyze"
								/>
								<p class="description"><?php esc_html_e('The plugin sends the uploaded image to this URL using multipart/form-data.', 'face-shape-analyzer'); ?></p>
							</td>
						</tr>

						<tr>
							<th scope="row">
								<label for="fsa-auth-type"><?php esc_html_e('Authentication type', 'face-shape-analyzer'); ?></label>
							</th>
							<td>
								<select id="fsa-auth-type" name="<?php echo esc_attr(self::OPTION_NAME); ?>[auth_type]">
									<option value="none" <?php selected($settings['auth_type'], 'none'); ?>><?php esc_html_e('None', 'face-shape-analyzer'); ?></option>
									<option value="bearer" <?php selected($settings['auth_type'], 'bearer'); ?>><?php esc_html_e('Bearer token', 'face-shape-analyzer'); ?></option>
									<option value="custom_header" <?php selected($settings['auth_type'], 'custom_header'); ?>><?php esc_html_e('Custom header', 'face-shape-analyzer'); ?></option>
								</select>
							</td>
						</tr>

						<tr>
							<th scope="row">
								<label for="fsa-api-key"><?php esc_html_e('API key / token', 'face-shape-analyzer'); ?></label>
							</th>
							<td>
								<input
									id="fsa-api-key"
									class="regular-text code"
									type="text"
									name="<?php echo esc_attr(self::OPTION_NAME); ?>[api_key]"
									value="<?php echo esc_attr($settings['api_key']); ?>"
								/>
								<p class="description"><?php esc_html_e('Used as the bearer token or custom header value.', 'face-shape-analyzer'); ?></p>
							</td>
						</tr>

						<tr>
							<th scope="row">
								<label for="fsa-auth-header"><?php esc_html_e('Custom header name', 'face-shape-analyzer'); ?></label>
							</th>
							<td>
								<input
									id="fsa-auth-header"
									class="regular-text code"
									type="text"
									name="<?php echo esc_attr(self::OPTION_NAME); ?>[auth_header_name]"
									value="<?php echo esc_attr($settings['auth_header_name']); ?>"
									placeholder="X-API-Key"
								/>
								<p class="description"><?php esc_html_e('Only used when authentication type is set to Custom header.', 'face-shape-analyzer'); ?></p>
							</td>
						</tr>

						<tr>
							<th scope="row">
								<label for="fsa-file-field"><?php esc_html_e('Image field name', 'face-shape-analyzer'); ?></label>
							</th>
							<td>
								<input
									id="fsa-file-field"
									class="regular-text code"
									type="text"
									name="<?php echo esc_attr(self::OPTION_NAME); ?>[file_field_name]"
									value="<?php echo esc_attr($settings['file_field_name']); ?>"
									placeholder="file"
								/>
								<p class="description"><?php esc_html_e('The multipart form field name expected by your API for the uploaded file.', 'face-shape-analyzer'); ?></p>
							</td>
						</tr>

						<tr>
							<th scope="row">
								<label for="fsa-extra-fields"><?php esc_html_e('Extra form fields (JSON)', 'face-shape-analyzer'); ?></label>
							</th>
							<td>
								<textarea
									id="fsa-extra-fields"
									class="large-text code"
									name="<?php echo esc_attr(self::OPTION_NAME); ?>[extra_fields_json]"
									rows="6"
									placeholder="{&quot;mode&quot;:&quot;full&quot;,&quot;user_id&quot;:&quot;123&quot;}"
								><?php echo esc_textarea($settings['extra_fields_json']); ?></textarea>
								<p class="description"><?php esc_html_e('Optional extra fields that should be sent with every API request. Provide a flat JSON object.', 'face-shape-analyzer'); ?></p>
							</td>
						</tr>

						<tr>
							<th scope="row">
								<label for="fsa-timeout"><?php esc_html_e('Request timeout (seconds)', 'face-shape-analyzer'); ?></label>
							</th>
							<td>
								<input
									id="fsa-timeout"
									class="small-text"
									type="number"
									min="5"
									max="120"
									name="<?php echo esc_attr(self::OPTION_NAME); ?>[timeout]"
									value="<?php echo esc_attr((string) $settings['timeout']); ?>"
								/>
							</td>
						</tr>

						<tr>
							<th scope="row">
								<label for="fsa-image-base"><?php esc_html_e('Image base URL', 'face-shape-analyzer'); ?></label>
							</th>
							<td>
								<input
									id="fsa-image-base"
									class="regular-text code"
									type="url"
									name="<?php echo esc_attr(self::OPTION_NAME); ?>[image_base_url]"
									value="<?php echo esc_attr($settings['image_base_url']); ?>"
									placeholder="https://api.example.com"
								/>
								<p class="description"><?php esc_html_e('Optional. Use this if the API returns relative image URLs like /image/file.jpg.', 'face-shape-analyzer'); ?></p>
							</td>
						</tr>
					</tbody>
				</table>

				<?php submit_button(__('Save Settings', 'face-shape-analyzer')); ?>
			</form>

			<hr />

			<h2><?php esc_html_e('Shortcode', 'face-shape-analyzer'); ?></h2>
			<p><code>[face_shape_analyzer]</code></p>
		</div>
		<?php
	}

	public function sanitize_settings($input) {
		$output = $this->get_default_settings();

		$output['endpoint_url'] = ! empty($input['endpoint_url']) ? esc_url_raw(trim((string) $input['endpoint_url'])) : '';

		$auth_type = ! empty($input['auth_type']) ? sanitize_key((string) $input['auth_type']) : 'none';
		if (! in_array($auth_type, array('none', 'bearer', 'custom_header'), true)) {
			$auth_type = 'none';
		}
		$output['auth_type'] = $auth_type;

		$output['api_key'] = ! empty($input['api_key']) ? sanitize_text_field((string) $input['api_key']) : '';
		$output['auth_header_name'] = ! empty($input['auth_header_name']) ? preg_replace('/[^A-Za-z0-9\-]/', '', (string) $input['auth_header_name']) : 'X-API-Key';
		$output['file_field_name'] = ! empty($input['file_field_name']) ? preg_replace('/[^A-Za-z0-9_\-]/', '', (string) $input['file_field_name']) : 'file';

		$timeout = isset($input['timeout']) ? (int) $input['timeout'] : 35;
		$output['timeout'] = min(120, max(5, $timeout));

		$output['image_base_url'] = ! empty($input['image_base_url']) ? esc_url_raw(trim((string) $input['image_base_url'])) : '';

		$extra_fields = isset($input['extra_fields_json']) ? trim((string) $input['extra_fields_json']) : '';
		if ('' !== $extra_fields) {
			$decoded = json_decode($extra_fields, true);

			if (! is_array($decoded) || JSON_ERROR_NONE !== json_last_error()) {
				add_settings_error(
					self::OPTION_NAME,
					'fsa-invalid-json',
					__('Extra form fields must be a valid JSON object.', 'face-shape-analyzer'),
					'error'
				);
				$extra_fields = '';
			} else {
				$sanitized = array();
				foreach ($decoded as $key => $value) {
					if (! is_scalar($value) || '' === $key) {
						continue;
					}

					$clean_key = preg_replace('/[^A-Za-z0-9_\-]/', '', (string) $key);
					if ('' === $clean_key) {
						continue;
					}

					$sanitized[$clean_key] = (string) $value;
				}

				$extra_fields = ! empty($sanitized) ? (string) wp_json_encode($sanitized, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) : '';
			}
		}

		$output['extra_fields_json'] = $extra_fields;

		return $output;
	}

	public function handle_process_request() {
		check_ajax_referer(self::NONCE_ACTION, 'nonce');

		if (empty($_FILES['image'])) {
			wp_send_json_error(
				array(
					'message' => __('Please choose an image before submitting.', 'face-shape-analyzer'),
				),
				400
			);
		}

		$image = $_FILES['image'];

		if (! empty($image['error'])) {
			wp_send_json_error(
				array(
					'message' => __('The image upload could not be processed.', 'face-shape-analyzer'),
				),
				400
			);
		}

		$allowed_types = array('image/jpeg', 'image/png', 'image/webp');
		$file_size = isset($image['size']) ? (int) $image['size'] : 0;
		$validated_type = wp_check_filetype_and_ext($image['tmp_name'], $image['name']);
		$file_type = ! empty($validated_type['type']) ? (string) $validated_type['type'] : '';

		if ($file_size > 8 * 1024 * 1024) {
			wp_send_json_error(
				array(
					'message' => __('Please upload an image smaller than 8MB.', 'face-shape-analyzer'),
				),
				400
			);
		}

		if (! in_array($file_type, $allowed_types, true)) {
			wp_send_json_error(
				array(
					'message' => __('Only JPG, PNG, and WEBP images are supported.', 'face-shape-analyzer'),
				),
				400
			);
		}

		$image['type'] = $file_type;

		$settings = $this->get_settings();
		if (empty($settings['endpoint_url'])) {
			wp_send_json_error(
				array(
					'message' => __('The API endpoint has not been configured yet.', 'face-shape-analyzer'),
				),
				500
			);
		}

		$api_response = $this->send_to_api($image, $settings);

		if (is_wp_error($api_response)) {
			wp_send_json_error(
				array(
					'message' => $api_response->get_error_message(),
				),
				500
			);
		}

		wp_send_json_success($this->normalize_api_response($api_response, $settings));
	}

	private function send_to_api(array $image, array $settings) {
		if (! function_exists('curl_init')) {
			return new WP_Error(
				'fsa-missing-curl',
				__('cURL is required on this server to send images to the analysis API.', 'face-shape-analyzer')
			);
		}

		$headers = array(
			'Accept: application/json',
			'Expect:',
		);

		$site_origin = untrailingslashit(home_url());
		if ('' !== $site_origin) {
			$headers[] = 'Origin: ' . $site_origin;
			$headers[] = 'Referer: ' . home_url('/');
		}

		if ('bearer' === $settings['auth_type'] && '' !== $settings['api_key']) {
			$headers[] = 'Authorization: Bearer ' . $settings['api_key'];
		}

		if ('custom_header' === $settings['auth_type'] && '' !== $settings['api_key']) {
			$headers[] = $settings['auth_header_name'] . ': ' . $settings['api_key'];
		}

		$fields = $this->get_extra_fields($settings['extra_fields_json']);
		$field_name = '' !== $settings['file_field_name'] ? $settings['file_field_name'] : 'file';

		$fields[$field_name] = curl_file_create(
			$image['tmp_name'],
			$image['type'],
			$image['name']
		);

		$curl = curl_init($settings['endpoint_url']);
		curl_setopt_array(
			$curl,
			array(
				CURLOPT_POST           => true,
				CURLOPT_POSTFIELDS     => $fields,
				CURLOPT_HTTPHEADER     => $headers,
				CURLOPT_RETURNTRANSFER => true,
				CURLOPT_TIMEOUT        => (int) $settings['timeout'],
				CURLOPT_CONNECTTIMEOUT => 15,
				CURLOPT_USERAGENT      => 'FaceShapeAnalyzer/' . self::VERSION . '; ' . home_url('/'),
			)
		);

		$raw_response = curl_exec($curl);
		$http_code = (int) curl_getinfo($curl, CURLINFO_RESPONSE_CODE);
		$curl_error = curl_error($curl);
		curl_close($curl);

		if (false === $raw_response) {
			return new WP_Error(
				'fsa-curl-error',
				$curl_error ? $curl_error : __('The API request failed before a response was received.', 'face-shape-analyzer')
			);
		}

		$decoded = json_decode($raw_response, true);
		if (! is_array($decoded)) {
			return new WP_Error(
				'fsa-invalid-response',
				__('The API response was not valid JSON.', 'face-shape-analyzer')
			);
		}

		if ($http_code >= 400) {
			$message = ! empty($decoded['message']) ? (string) $decoded['message'] : __('The API returned an error.', 'face-shape-analyzer');
			if (! empty($decoded['detail'])) {
				$message .= ': ' . (string) $decoded['detail'];
			}

			return new WP_Error(
				'fsa-api-error',
				sprintf(
					/* translators: 1: HTTP status code, 2: API error message. */
					__('API error %1$d: %2$s', 'face-shape-analyzer'),
					$http_code,
					$message
				)
			);
		}

		if (array_key_exists('success', $decoded) && false === $decoded['success']) {
			$message = ! empty($decoded['message']) ? (string) $decoded['message'] : __('The API could not analyze this portrait.', 'face-shape-analyzer');
			return new WP_Error('fsa-analysis-failed', $message);
		}

		return $decoded;
	}

	private function normalize_api_response(array $payload, array $settings) {
		$base_source = ! empty($settings['image_base_url']) ? $settings['image_base_url'] : $settings['endpoint_url'];

		if (! empty($payload['images']) && is_array($payload['images'])) {
			foreach (array('original_url', 'highlighted_url') as $key) {
				if (empty($payload['images'][$key]) || ! is_string($payload['images'][$key])) {
					continue;
				}

				$payload['images'][$key] = $this->to_absolute_url($payload['images'][$key], $base_source);
			}
		}

		return $payload;
	}

	private function to_absolute_url($maybe_url, $base_source) {
		if (preg_match('#^https?://#i', $maybe_url)) {
			return esc_url_raw($maybe_url);
		}

		$parts = wp_parse_url($base_source);
		if (! is_array($parts) || empty($parts['scheme']) || empty($parts['host'])) {
			return $maybe_url;
		}

		$base = $parts['scheme'] . '://' . $parts['host'];
		if (! empty($parts['port'])) {
			$base .= ':' . $parts['port'];
		}

		return esc_url_raw(trailingslashit($base) . ltrim($maybe_url, '/'));
	}

	private function get_extra_fields($raw_json) {
		if (empty($raw_json)) {
			return array();
		}

		$decoded = json_decode((string) $raw_json, true);
		return is_array($decoded) ? $decoded : array();
	}

	private function get_settings() {
		return wp_parse_args(get_option(self::OPTION_NAME, array()), $this->get_default_settings());
	}

	private function get_default_settings() {
		return array(
			'endpoint_url'     => '',
			'auth_type'        => 'none',
			'api_key'          => '',
			'auth_header_name' => 'X-API-Key',
			'file_field_name'  => 'file',
			'extra_fields_json'=> '',
			'timeout'          => 35,
			'image_base_url'   => '',
		);
	}

	private function get_tab_definitions() {
		return array(
			array(
				'slug'  => 'shape',
				'label' => __('Shape', 'face-shape-analyzer'),
			),
			array(
				'slug'  => 'score',
				'label' => __('Score', 'face-shape-analyzer'),
			),
			array(
				'slug'  => 'eyes',
				'label' => __('Eyes', 'face-shape-analyzer'),
			),
			array(
				'slug'  => 'brows',
				'label' => __('Brows', 'face-shape-analyzer'),
			),
			array(
				'slug'  => 'lips',
				'label' => __('Lips', 'face-shape-analyzer'),
			),
			array(
				'slug'  => 'nose',
				'label' => __('Nose', 'face-shape-analyzer'),
			),
		);
	}

	private function get_icon_markup($slug) {
		$icons = array(
			'shape' => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.75a4.5 4.5 0 0 0-4.5 4.5v2.5a6.5 6.5 0 0 1-1.9 4.6L4.8 15.2a2 2 0 0 0 1.4 3.4h11.6a2 2 0 0 0 1.4-3.4l-.8-.85a6.5 6.5 0 0 1-1.9-4.6v-2.5a4.5 4.5 0 0 0-4.5-4.5Z"/><path d="M9.5 20.5a2.5 2.5 0 0 0 5 0"/></svg>',
			'score' => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m12 2.8 2.5 5 5.5.8-4 3.9.9 5.5-4.9-2.6-4.9 2.6.9-5.5-4-3.9 5.5-.8 2.5-5Z"/></svg>',
			'eyes'  => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.8-6 10-6 10 6 10 6-3.8 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.8"/></svg>',
			'brows' => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5c1.8-1.8 4-2.7 6.4-2.7 2.5 0 4.3.7 6.1 2.4"/><path d="M8.5 13.4a2.6 2.6 0 1 1 0-5.2 2.6 2.6 0 0 1 0 5.2Z"/><path d="M15.5 7.8c2.4 0 4.6.9 5.5 2.7"/><path d="M15.5 13.4a2.6 2.6 0 1 1 0-5.2 2.6 2.6 0 0 1 0 5.2Z"/></svg>',
			'lips'  => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12s3.2-4 9-4 9 4 9 4-3.2 4-9 4-9-4-9-4Z"/><path d="M5.5 12s2 2.8 6.5 2.8 6.5-2.8 6.5-2.8"/></svg>',
			'nose'  => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10.6 4.5c.4 3.8-.1 7.2-1.6 10.2-.6 1.3-.2 2.9 1.5 3.6 1.7.6 4.3.3 6-.8"/><path d="M10 19.8c1.8 1 3.8 1 5.9 0"/></svg>',
		);

		return isset($icons[$slug]) ? $icons[$slug] : '';
	}
}

new FSA_Face_Shape_Analyzer();

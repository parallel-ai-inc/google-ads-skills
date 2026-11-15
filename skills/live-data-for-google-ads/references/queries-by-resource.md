<!-- Generated 2026-11-14 from the queries Parallel AI's own agent runs. Do not edit by hand. -->

# Google Ads queries by resource

Each section lists the fields our product selects from one resource, across all of its queries on that resource. Every field listed is real and selectable from that resource. Fields taken from different queries are not guaranteed to combine in one query, because some metrics and segments exclude each other. Check a new combination with the metadata tool before relying on it. A field that is not listed may still be valid.

Resources covered: 92.

## account_budget

**Fields:** `account_budget.adjusted_spending_limit_micros`, `account_budget.adjusted_spending_limit_type`, `account_budget.amount_served_micros`, `account_budget.approved_end_date_time`, `account_budget.approved_end_time_type`, `account_budget.approved_spending_limit_micros`, `account_budget.approved_spending_limit_type`, `account_budget.approved_start_date_time`, `account_budget.billing_setup`, `account_budget.id`, `account_budget.name`, `account_budget.notes`, `account_budget.pending_proposal.account_budget_proposal`, `account_budget.pending_proposal.creation_date_time`, `account_budget.pending_proposal.end_date_time`, `account_budget.pending_proposal.end_time_type`, `account_budget.pending_proposal.name`, `account_budget.pending_proposal.notes`, `account_budget.pending_proposal.proposal_type`, `account_budget.pending_proposal.purchase_order_number`, `account_budget.pending_proposal.spending_limit_micros`, `account_budget.pending_proposal.spending_limit_type`, `account_budget.pending_proposal.start_date_time`, `account_budget.proposed_end_date_time`, `account_budget.proposed_end_time_type`, `account_budget.proposed_spending_limit_micros`, `account_budget.proposed_spending_limit_type`, `account_budget.proposed_start_date_time`, `account_budget.purchase_order_number`, `account_budget.resource_name`, `account_budget.status`, `account_budget.total_adjustments_micros`

**Filters used:** `account_budget.billing_setup =`, `account_budget.status =`

## account_budget_proposal

**Fields:** `account_budget_proposal.account_budget`, `account_budget_proposal.approval_date_time`, `account_budget_proposal.approved_end_date_time`, `account_budget_proposal.approved_end_time_type`, `account_budget_proposal.approved_spending_limit_micros`, `account_budget_proposal.approved_spending_limit_type`, `account_budget_proposal.approved_start_date_time`, `account_budget_proposal.billing_setup`, `account_budget_proposal.creation_date_time`, `account_budget_proposal.id`, `account_budget_proposal.proposal_type`, `account_budget_proposal.proposed_end_date_time`, `account_budget_proposal.proposed_end_time_type`, `account_budget_proposal.proposed_name`, `account_budget_proposal.proposed_notes`, `account_budget_proposal.proposed_purchase_order_number`, `account_budget_proposal.proposed_spending_limit_micros`, `account_budget_proposal.proposed_spending_limit_type`, `account_budget_proposal.proposed_start_date_time`, `account_budget_proposal.resource_name`, `account_budget_proposal.status`

**Filters used:** `account_budget_proposal.account_budget =`, `account_budget_proposal.billing_setup =`, `account_budget_proposal.proposal_type IN`, `account_budget_proposal.status IN`

## account_link

**Fields:** `account_link.account_link_id`, `account_link.resource_name`, `account_link.status`, `account_link.third_party_app_analytics.app_analytics_provider_id`, `account_link.third_party_app_analytics.app_id`, `account_link.third_party_app_analytics.app_vendor`, `account_link.type`

**Filters used:** `account_link.status =`, `account_link.third_party_app_analytics.app_analytics_provider_id =`, `account_link.third_party_app_analytics.app_id =`, `account_link.third_party_app_analytics.app_vendor =`, `account_link.type =`

**Ordered by:** `account_link.account_link_id DESC`

## ad_group

**Fields:** `ad_group.ad_rotation_mode`, `ad_group.ai_max_ad_group_setting.disable_search_term_matching`, `ad_group.audience_setting.use_audience_grouped`, `ad_group.base_ad_group`, `ad_group.campaign`, `ad_group.cpc_bid_micros`, `ad_group.cpm_bid_micros`, `ad_group.cpv_bid_micros`, `ad_group.demand_gen_ad_group_settings.channel_controls.channel_config`, `ad_group.demand_gen_ad_group_settings.channel_controls.channel_strategy`, `ad_group.demand_gen_ad_group_settings.channel_controls.selected_channels.discover`, `ad_group.demand_gen_ad_group_settings.channel_controls.selected_channels.display`, `ad_group.demand_gen_ad_group_settings.channel_controls.selected_channels.gmail`, `ad_group.demand_gen_ad_group_settings.channel_controls.selected_channels.maps`, `ad_group.demand_gen_ad_group_settings.channel_controls.selected_channels.youtube_in_feed`, `ad_group.demand_gen_ad_group_settings.channel_controls.selected_channels.youtube_in_stream`, `ad_group.demand_gen_ad_group_settings.channel_controls.selected_channels.youtube_shorts`, `ad_group.display_custom_bid_dimension`, `ad_group.effective_cpc_bid_micros`, `ad_group.effective_target_cpa_micros`, `ad_group.effective_target_cpa_source`, `ad_group.effective_target_cpc`, `ad_group.effective_target_cpc_source`, `ad_group.effective_target_roas`, `ad_group.effective_target_roas_source`, `ad_group.exclude_demographic_expansion`, `ad_group.excluded_parent_asset_field_types`, `ad_group.excluded_parent_asset_set_types`, `ad_group.final_url_suffix`, `ad_group.fixed_cpm_micros`, `ad_group.id`, `ad_group.labels`, `ad_group.name`, `ad_group.optimized_targeting_enabled`, `ad_group.percent_cpc_bid_micros`, `ad_group.primary_status`, `ad_group.primary_status_reasons`, `ad_group.resource_name`, `ad_group.status`, `ad_group.target_cpa_micros`, `ad_group.target_cpc_micros`, `ad_group.target_cpm_micros`, `ad_group.target_cpv_micros`, `ad_group.target_roas`, `ad_group.targeting_setting.target_restrictions`, `ad_group.tracking_url_template`, `ad_group.type`, `ad_group.url_custom_parameters`, `ad_group.vertical_ads_format_setting.disable_text_ads`, `ad_group.vertical_ads_format_setting.enable_booking_links`, `ad_group.vertical_ads_format_setting.enable_vertical_promotion_ads`, `ad_group.video_ad_group_settings.video_ad_sequence.step_id`, `campaign.id`, `campaign.name`, `campaign.status`, `customer.currency_code`, `metrics.*`, `metrics.all_conversions`, `metrics.average_cpc`, `metrics.clicks`, `metrics.conversions`, `metrics.conversions_value`, `metrics.cost_micros`, `metrics.cost_per_conversion`, `metrics.ctr`, `metrics.impressions`, `segments.*`

**Filters used:** `ad_group.campaign =`, `ad_group.campaign IN`, `ad_group.id IN`, `ad_group.name =`, `ad_group.name IN`, `ad_group.resource_name =`, `ad_group.status !=`, `ad_group.status =`, `ad_group.status IN`, `campaign.status !=`, `metrics.clicks >=`, `metrics.impressions >=`, `segments.date DURING`

**Date field:** `segments.date`

**Ordered by:** `ad_group.id ASC`, `ad_group.name ASC`, `metrics.cost_micros DESC`

## ad_group_ad

**Fields:** `ad_group_ad.ad.added_by_google_ads`, `ad_group_ad.ad.expanded_text_ad.description`, `ad_group_ad.ad.expanded_text_ad.headline_part1`, `ad_group_ad.ad.expanded_text_ad.headline_part2`, `ad_group_ad.ad.final_urls`, `ad_group_ad.ad.id`, `ad_group_ad.ad.name`, `ad_group_ad.ad.responsive_search_ad.descriptions`, `ad_group_ad.ad.responsive_search_ad.headlines`, `ad_group_ad.ad.system_managed_resource_source`, `ad_group_ad.ad.type`, `ad_group_ad.ad_group`, `ad_group_ad.ad_group_ad_asset_automation_settings`, `ad_group_ad.policy_summary.approval_status`, `ad_group_ad.policy_summary.policy_topic_entries`, `ad_group_ad.policy_summary.review_status`, `ad_group_ad.primary_status`, `ad_group_ad.resource_name`, `ad_group_ad.status`, `metrics.*`, `segments.*`

**Filters used:** `ad_group.id IN`, `ad_group.status !=`, `ad_group_ad.ad.id !=`, `ad_group_ad.ad.id =`, `ad_group_ad.ad.id IN`, `ad_group_ad.ad.type =`, `ad_group_ad.ad_group =`, `ad_group_ad.ad_group IN`, `ad_group_ad.policy_summary.approval_status =`, `ad_group_ad.policy_summary.approval_status IN`, `ad_group_ad.policy_summary.review_status IN`, `ad_group_ad.resource_name IN`, `ad_group_ad.status !=`, `ad_group_ad.status IN`, `campaign.id =`, `campaign.id IN`

**Date field:** `segments.date`

**Ordered by:** `ad_group_ad.ad.id ASC`, `ad_group_ad.ad.id DESC`

## ad_group_ad_asset_view

**Fields:** `ad_group_ad_asset_view.ad_group_ad`, `ad_group_ad_asset_view.asset`, `ad_group_ad_asset_view.enabled`, `ad_group_ad_asset_view.field_type`, `ad_group_ad_asset_view.performance_label`, `ad_group_ad_asset_view.policy_summary`, `ad_group_ad_asset_view.resource_name`, `asset.id`, `asset.name`, `asset.source`, `asset.type`, `metrics.clicks`, `metrics.cost_micros`, `metrics.impressions`

**Filters used:** `ad_group.status !=`, `ad_group_ad.status !=`, `ad_group_ad_asset_view.ad_group_ad IN`, `ad_group_ad_asset_view.asset IN`, `ad_group_ad_asset_view.field_type IN`, `ad_group_ad_asset_view.performance_label IN`, `segments.date DURING`

## ad_group_ad_label

**Fields:** `ad_group_ad_label.label`, `label.id`, `label.name`, `label.status`

**Filters used:** `ad_group_ad_label.ad_group_ad =`

**Ordered by:** `label.name ASC`

## ad_group_audience_view

**Fields:** `ad_group.name`, `ad_group_audience_view.resource_name`, `campaign.id`, `campaign.name`, `metrics.clicks`, `metrics.conversions`, `metrics.conversions_value`, `metrics.cost_micros`, `metrics.impressions`

**Filters used:** `campaign.id IN`, `metrics.impressions >=`

**Date field:** `segments.date`

**Ordered by:** `metrics.impressions DESC`

## ad_group_bid_modifier

**Fields:** `ad_group_bid_modifier.ad_group`, `ad_group_bid_modifier.bid_modifier`, `ad_group_bid_modifier.criterion_id`, `ad_group_bid_modifier.device.type`

**Filters used:** `ad_group_bid_modifier.ad_group =`

## ad_group_criterion

**Fields:** `ad_group.audience_setting.use_audience_grouped`, `ad_group.id`, `ad_group.name`, `ad_group.resource_name`, `ad_group.status`, `ad_group.targeting_setting.target_restrictions`, `ad_group_criterion.ad_group`, `ad_group_criterion.age_range.type`, `ad_group_criterion.audience.audience`, `ad_group_criterion.bid_modifier`, `ad_group_criterion.brand_list.shared_set`, `ad_group_criterion.combined_audience.combined_audience`, `ad_group_criterion.cpc_bid_micros`, `ad_group_criterion.criterion_id`, `ad_group_criterion.custom_affinity.custom_affinity`, `ad_group_criterion.custom_audience.custom_audience`, `ad_group_criterion.custom_intent.custom_intent`, `ad_group_criterion.effective_cpc_bid_micros`, `ad_group_criterion.effective_cpc_bid_source`, `ad_group_criterion.final_mobile_urls`, `ad_group_criterion.final_url_suffix`, `ad_group_criterion.final_urls`, `ad_group_criterion.gender.type`, `ad_group_criterion.income_range.type`, `ad_group_criterion.keyword.match_type`, `ad_group_criterion.keyword.text`, `ad_group_criterion.labels`, `ad_group_criterion.life_event.life_event_id`, `ad_group_criterion.mobile_app_category.mobile_app_category_constant`, `ad_group_criterion.negative`, `ad_group_criterion.parental_status.type`, `ad_group_criterion.placement.url`, `ad_group_criterion.position_estimates.estimated_add_clicks_at_first_position_cpc`, `ad_group_criterion.position_estimates.estimated_add_cost_at_first_position_cpc`, `ad_group_criterion.position_estimates.first_page_cpc_micros`, `ad_group_criterion.position_estimates.first_position_cpc_micros`, `ad_group_criterion.position_estimates.top_of_page_cpc_micros`, `ad_group_criterion.primary_status`, `ad_group_criterion.primary_status_reasons`, `ad_group_criterion.quality_info.creative_quality_score`, `ad_group_criterion.quality_info.post_click_quality_score`, `ad_group_criterion.quality_info.quality_score`, `ad_group_criterion.quality_info.search_predicted_ctr`, `ad_group_criterion.resource_name`, `ad_group_criterion.status`, `ad_group_criterion.system_serving_status`, `ad_group_criterion.topic.topic_constant`, `ad_group_criterion.tracking_url_template`, `ad_group_criterion.type`, `ad_group_criterion.url_custom_parameters`, `ad_group_criterion.user_interest.user_interest_category`, `ad_group_criterion.user_list.user_list`, `ad_group_criterion.webpage.conditions`, `ad_group_criterion.webpage.criterion_name`, `ad_group_criterion.youtube_channel.channel_id`, `ad_group_criterion.youtube_video.video_id`, `campaign.id`, `campaign.name`, `campaign.resource_name`, `campaign.status`, `metrics.average_cpc`, `metrics.clicks`, `metrics.conversions`, `metrics.conversions_from_interactions_rate`, `metrics.cost_micros`, `metrics.cost_per_conversion`, `metrics.ctr`, `metrics.impressions`

**Filters used:** `ad_group.id =`, `ad_group.status !=`, `ad_group_criterion.ad_group =`, `ad_group_criterion.ad_group IN`, `ad_group_criterion.criterion_id =`, `ad_group_criterion.criterion_id IN`, `ad_group_criterion.keyword.match_type =`, `ad_group_criterion.keyword.match_type IN`, `ad_group_criterion.keyword.text =`, `ad_group_criterion.keyword.text LIKE`, `ad_group_criterion.negative =`, `ad_group_criterion.resource_name =`, `ad_group_criterion.resource_name IN`, `ad_group_criterion.status !=`, `ad_group_criterion.status IN`, `ad_group_criterion.type =`, `ad_group_criterion.type IN`, `campaign.id =`, `campaign.status !=`, `metrics.average_cpc <=`, `metrics.average_cpc >=`, `metrics.clicks <=`, `metrics.clicks >=`, `metrics.conversions <=`, `metrics.conversions >=`, `metrics.conversions_from_interactions_rate <=`, `metrics.conversions_from_interactions_rate >=`, `metrics.cost_micros <=`, `metrics.cost_micros >=`, `metrics.cost_per_conversion <=`, `metrics.cost_per_conversion >=`, `metrics.ctr <=`, `metrics.ctr >=`, `metrics.impressions <=`, `metrics.impressions >=`

**Date field:** `segments.date`

**Ordered by:** `ad_group.id ASC`, `ad_group_criterion.keyword.text ASC`

## ad_group_criterion_customizer

**Fields:** `ad_group.id`, `ad_group.name`, `ad_group.resource_name`, `ad_group_criterion.criterion_id`, `ad_group_criterion.keyword.match_type`, `ad_group_criterion.keyword.text`, `ad_group_criterion.resource_name`, `ad_group_criterion.type`, `ad_group_criterion_customizer.ad_group_criterion`, `ad_group_criterion_customizer.customizer_attribute`, `ad_group_criterion_customizer.resource_name`, `ad_group_criterion_customizer.status`, `ad_group_criterion_customizer.value.string_value`, `ad_group_criterion_customizer.value.type`, `campaign.id`, `campaign.name`, `campaign.resource_name`, `customizer_attribute.id`, `customizer_attribute.name`, `customizer_attribute.resource_name`, `customizer_attribute.status`, `customizer_attribute.type`

**Filters used:** `ad_group.resource_name =`, `ad_group_criterion.criterion_id =`, `ad_group_criterion.resource_name =`, `ad_group_criterion_customizer.customizer_attribute =`, `ad_group_criterion_customizer.status !=`, `campaign.resource_name =`

## ad_group_criterion_label

**Fields:** `ad_group_criterion_label.label`, `label.id`, `label.name`, `label.status`

**Filters used:** `ad_group_criterion_label.ad_group_criterion =`

**Ordered by:** `label.name ASC`

## ad_group_customizer

**Fields:** `ad_group.id`, `ad_group.name`, `ad_group.resource_name`, `ad_group_customizer.ad_group`, `ad_group_customizer.customizer_attribute`, `ad_group_customizer.resource_name`, `ad_group_customizer.status`, `ad_group_customizer.value.string_value`, `ad_group_customizer.value.type`, `campaign.id`, `campaign.name`, `campaign.resource_name`, `customizer_attribute.id`, `customizer_attribute.name`, `customizer_attribute.resource_name`, `customizer_attribute.status`, `customizer_attribute.type`

**Filters used:** `ad_group.resource_name =`, `ad_group_customizer.customizer_attribute =`, `ad_group_customizer.status !=`, `campaign.resource_name =`

## ad_group_label

**Fields:** `ad_group_label.label`, `label.id`, `label.name`, `label.status`

**Filters used:** `ad_group_label.ad_group =`

**Ordered by:** `label.name ASC`

## ad_parameter

**Fields:** `ad_parameter.ad_group_criterion`, `ad_parameter.insertion_text`, `ad_parameter.parameter_index`, `ad_parameter.resource_name`

**Filters used:** `ad_parameter.ad_group_criterion =`, `ad_parameter.parameter_index =`

**Ordered by:** `ad_parameter.parameter_index ASC`

## age_range_view|gender_view|parental_status_view

**Fields:** `ad_group_criterion.age_range.type`, `ad_group_criterion.bid_modifier`, `ad_group_criterion.gender.type`, `ad_group_criterion.parental_status.type`, `campaign.id`, `campaign.name`, `metrics.clicks`, `metrics.conversions`, `metrics.cost_micros`, `metrics.ctr`, `metrics.impressions`

**Filters used:** `campaign.id =`

**Date field:** `segments.date`

**Ordered by:** `metrics.impressions DESC`

## applied_incentive

**Fields:** `applied_incentive.coupon_code`, `applied_incentive.currency_code`, `applied_incentive.current_spend_towards_fulfillment_micros`, `applied_incentive.fulfillment_expiration_date_time`, `applied_incentive.granted_amount_micros`, `applied_incentive.incentive_state`, `applied_incentive.redemption_date_time`, `applied_incentive.required_min_spend_micros`, `applied_incentive.resource_name`, `applied_incentive.reward_amount_micros`, `applied_incentive.reward_balance_remaining_micros`, `applied_incentive.reward_expiration_date_time`, `applied_incentive.reward_grant_date_time`

**Filters used:** `applied_incentive.coupon_code =`, `applied_incentive.incentive_state =`

**Ordered by:** `applied_incentive.reward_grant_date_time DESC`

## asset

**Fields:** `asset.id`, `asset.image_asset.full_size.url`, `asset.name`, `asset.policy_summary.approval_status`, `asset.policy_summary.policy_topic_entries`, `asset.policy_summary.review_status`, `asset.resource_name`, `asset.source`, `asset.text_asset.text`, `asset.type`, `asset.youtube_video_asset.youtube_video_id`

**Filters used:** `asset.name =`, `asset.name LIKE`, `asset.resource_name IN`, `asset.type IN`

**Ordered by:** `asset.type ASC`

## asset_group

**Fields:** `asset_group.ad_strength`, `asset_group.asset_coverage.ad_strength_action_items`, `asset_group.campaign`, `asset_group.final_mobile_urls`, `asset_group.final_url_suffix`, `asset_group.final_urls`, `asset_group.id`, `asset_group.name`, `asset_group.path1`, `asset_group.path2`, `asset_group.primary_status`, `asset_group.primary_status_reasons`, `asset_group.resource_name`, `asset_group.status`, `asset_group.tracking_url_template`, `asset_group.url_custom_parameters`, `metrics.*`, `metrics.average_cpc`, `metrics.clicks`, `metrics.conversions`, `metrics.conversions_value`, `metrics.cost_micros`, `metrics.cost_per_conversion`, `metrics.ctr`, `metrics.impressions`

**Filters used:** `asset_group.campaign =`, `asset_group.id =`, `asset_group.resource_name =`, `asset_group.status =`, `asset_group.status IN`, `metrics.impressions >=`

**Date field:** `segments.date`

**Ordered by:** `asset_group.name ASC`, `metrics.impressions DESC`

## asset_group_asset

**Fields:** `asset_group_asset.asset`, `asset_group_asset.asset_group`, `asset_group_asset.field_type`, `asset_group_asset.policy_summary.approval_status`, `asset_group_asset.policy_summary.policy_topic_entries`, `asset_group_asset.policy_summary.review_status`, `asset_group_asset.primary_status`, `asset_group_asset.primary_status_details`, `asset_group_asset.primary_status_reasons`, `asset_group_asset.resource_name`, `asset_group_asset.source`, `asset_group_asset.status`

**Filters used:** `asset_group_asset.asset_group =`, `asset_group_asset.asset_group IN`, `asset_group_asset.field_type =`

**Date field:** `segments.date`

**Ordered by:** `asset_group_asset.field_type ASC`

## asset_group_listing_group_filter

**Fields:** `asset_group_listing_group_filter.asset_group`, `asset_group_listing_group_filter.case_value.product_brand.value`, `asset_group_listing_group_filter.case_value.product_category.category_id`, `asset_group_listing_group_filter.case_value.product_category.level`, `asset_group_listing_group_filter.case_value.product_channel.channel`, `asset_group_listing_group_filter.case_value.product_condition.condition`, `asset_group_listing_group_filter.case_value.product_custom_attribute.index`, `asset_group_listing_group_filter.case_value.product_custom_attribute.value`, `asset_group_listing_group_filter.case_value.product_item_id.value`, `asset_group_listing_group_filter.case_value.product_type.level`, `asset_group_listing_group_filter.case_value.product_type.value`, `asset_group_listing_group_filter.listing_source`, `asset_group_listing_group_filter.parent_listing_group_filter`, `asset_group_listing_group_filter.resource_name`, `asset_group_listing_group_filter.type`

**Filters used:** `asset_group_listing_group_filter.asset_group IN`

## asset_group_product_group_view

**Fields:** `asset_group.id`, `asset_group.name`, `asset_group_listing_group_filter.case_value.product_brand.value`, `asset_group_listing_group_filter.case_value.product_category.category_id`, `asset_group_listing_group_filter.case_value.product_category.level`, `asset_group_listing_group_filter.case_value.product_channel.channel`, `asset_group_listing_group_filter.case_value.product_condition.condition`, `asset_group_listing_group_filter.case_value.product_custom_attribute.index`, `asset_group_listing_group_filter.case_value.product_custom_attribute.value`, `asset_group_listing_group_filter.case_value.product_item_id.value`, `asset_group_listing_group_filter.case_value.product_type.level`, `asset_group_listing_group_filter.case_value.product_type.value`, `asset_group_listing_group_filter.case_value.retail_filter_bundle.shared_set`, `asset_group_listing_group_filter.case_value.webpage.conditions`, `asset_group_listing_group_filter.id`, `asset_group_listing_group_filter.listing_source`, `asset_group_listing_group_filter.parent_listing_group_filter`, `asset_group_listing_group_filter.type`, `asset_group_product_group_view.asset_group`, `asset_group_product_group_view.asset_group_listing_group_filter`, `asset_group_product_group_view.resource_name`, `campaign.id`, `campaign.name`, `customer.currency_code`, `customer.time_zone`, `metrics.all_conversions`, `metrics.all_conversions_value`, `metrics.clicks`, `metrics.conversions`, `metrics.conversions_value`, `metrics.cost_micros`, `metrics.impressions`

**Filters used:** `asset_group.id =`, `asset_group_listing_group_filter.id =`, `campaign.advertising_channel_type =`, `campaign.id =`

**Date field:** `segments.date`

## asset_group_signal

**Fields:** `asset_group_signal.approval_status`, `asset_group_signal.asset_group`, `asset_group_signal.audience.audience`, `asset_group_signal.disapproval_reasons`, `asset_group_signal.resource_name`, `asset_group_signal.search_theme.text`

**Filters used:** `asset_group_signal.asset_group IN`

## asset_group_top_combination_view

**Fields:** `asset_group.id`, `asset_group.name`, `asset_group_top_combination_view.asset_group_top_combinations`, `asset_group_top_combination_view.resource_name`, `campaign.id`, `campaign.name`, `customer.time_zone`

**Filters used:** `asset_group.id =`, `campaign.advertising_channel_type =`, `campaign.id =`

**Date field:** `segments.date`

## asset_set

**Fields:** `asset_set.id`, `asset_set.name`, `asset_set.resource_name`, `asset_set.status`, `asset_set.type`

**Filters used:** `asset_set.status !=`, `asset_set.status IN`, `asset_set.type IN`

**Ordered by:** `asset_set.name ASC`

## asset_set_asset

**Fields:** `asset_set_asset.asset`, `asset_set_asset.asset_set`, `asset_set_asset.resource_name`, `asset_set_asset.status`

**Filters used:** `asset_set_asset.asset =`, `asset_set_asset.asset_set =`, `asset_set_asset.status =`

**Ordered by:** `asset_set_asset.status ASC`

## audience

**Fields:** `asset_group.name`, `asset_group.resource_name`, `audience.asset_group`, `audience.description`, `audience.dimensions`, `audience.exclusion_dimension`, `audience.id`, `audience.name`, `audience.resource_name`, `audience.scope`, `audience.status`

**Filters used:** `audience.id =`, `audience.status !=`, `audience.status =`

**Ordered by:** `audience.name ASC`

## batch_job

**Fields:** `batch_job.id`, `batch_job.metadata.completion_date_time`, `batch_job.metadata.creation_date_time`, `batch_job.metadata.estimated_completion_ratio`, `batch_job.metadata.executed_operation_count`, `batch_job.metadata.operation_count`, `batch_job.metadata.start_date_time`, `batch_job.next_add_sequence_token`, `batch_job.resource_name`, `batch_job.status`

**Filters used:** `batch_job.id =`

**Ordered by:** `batch_job.metadata.creation_date_time DESC`

## bidding_data_exclusion

**Fields:** `bidding_data_exclusion.advertising_channel_types`, `bidding_data_exclusion.campaigns`, `bidding_data_exclusion.data_exclusion_id`, `bidding_data_exclusion.devices`, `bidding_data_exclusion.end_date_time`, `bidding_data_exclusion.name`, `bidding_data_exclusion.resource_name`, `bidding_data_exclusion.scope`, `bidding_data_exclusion.start_date_time`, `bidding_data_exclusion.status`

**Filters used:** `bidding_data_exclusion.scope =`, `bidding_data_exclusion.status =`

## bidding_seasonality_adjustment

**Fields:** `bidding_seasonality_adjustment.advertising_channel_types`, `bidding_seasonality_adjustment.campaigns`, `bidding_seasonality_adjustment.conversion_rate_modifier`, `bidding_seasonality_adjustment.description`, `bidding_seasonality_adjustment.devices`, `bidding_seasonality_adjustment.end_date_time`, `bidding_seasonality_adjustment.name`, `bidding_seasonality_adjustment.resource_name`, `bidding_seasonality_adjustment.scope`, `bidding_seasonality_adjustment.seasonality_adjustment_id`, `bidding_seasonality_adjustment.start_date_time`, `bidding_seasonality_adjustment.status`

**Filters used:** `bidding_seasonality_adjustment.scope =`, `bidding_seasonality_adjustment.status =`

## bidding_strategy

**Fields:** `bidding_strategy.campaign_count`, `bidding_strategy.effective_currency_code`, `bidding_strategy.id`, `bidding_strategy.maximize_conversion_value.cpc_bid_ceiling_micros`, `bidding_strategy.maximize_conversion_value.cpc_bid_floor_micros`, `bidding_strategy.maximize_conversion_value.target_roas`, `bidding_strategy.maximize_conversion_value.target_roas_tolerance_percent_millis`, `bidding_strategy.maximize_conversions.cpc_bid_ceiling_micros`, `bidding_strategy.maximize_conversions.cpc_bid_floor_micros`, `bidding_strategy.maximize_conversions.target_cpa_micros`, `bidding_strategy.name`, `bidding_strategy.non_removed_campaign_count`, `bidding_strategy.resource_name`, `bidding_strategy.status`, `bidding_strategy.target_cpa.cpc_bid_ceiling_micros`, `bidding_strategy.target_cpa.cpc_bid_floor_micros`, `bidding_strategy.target_cpa.target_cpa_micros`, `bidding_strategy.target_impression_share.cpc_bid_ceiling_micros`, `bidding_strategy.target_impression_share.location`, `bidding_strategy.target_impression_share.location_fraction_micros`, `bidding_strategy.target_roas.cpc_bid_ceiling_micros`, `bidding_strategy.target_roas.cpc_bid_floor_micros`, `bidding_strategy.target_roas.target_roas`, `bidding_strategy.target_roas.target_roas_tolerance_percent_millis`, `bidding_strategy.target_spend.cpc_bid_ceiling_micros`, `bidding_strategy.type`

**Filters used:** `bidding_strategy.id =`, `bidding_strategy.status =`, `bidding_strategy.type =`

## billing_setup

**Fields:** `billing_setup.end_date_time`, `billing_setup.id`, `billing_setup.payments_account`, `billing_setup.payments_account_info.payments_account_id`, `billing_setup.payments_account_info.payments_account_name`, `billing_setup.payments_account_info.payments_profile_id`, `billing_setup.payments_account_info.payments_profile_name`, `billing_setup.resource_name`, `billing_setup.start_date_time`, `billing_setup.status`

**Ordered by:** `billing_setup.id ASC`

## campaign

**Fields:** `ad_group.id`, `ad_group.name`, `campaign.advertising_channel_sub_type`, `campaign.advertising_channel_type`, `campaign.asset_automation_settings`, `campaign.bidding_strategy`, `campaign.bidding_strategy_type`, `campaign.campaign_budget`, `campaign.commission.commission_rate_micros`, `campaign.contains_eu_political_advertising`, `campaign.end_date_time`, `campaign.final_url_suffix`, `campaign.fixed_cpm.goal`, `campaign.fixed_cpm.target_frequency_info.target_count`, `campaign.fixed_cpm.target_frequency_info.time_unit`, `campaign.geo_target_type_setting.negative_geo_target_type`, `campaign.geo_target_type_setting.positive_geo_target_type`, `campaign.id`, `campaign.manual_cpc.enhanced_cpc_enabled`, `campaign.maximize_conversion_value.target_roas`, `campaign.maximize_conversion_value.target_roas_tolerance_percent_millis`, `campaign.maximize_conversions.target_cpa_micros`, `campaign.name`, `campaign.network_settings.target_content_network`, `campaign.network_settings.target_google_search`, `campaign.network_settings.target_google_tv_network`, `campaign.network_settings.target_partner_search_network`, `campaign.network_settings.target_search_network`, `campaign.network_settings.target_youtube`, `campaign.optimization_score`, `campaign.percent_cpc.cpc_bid_ceiling_micros`, `campaign.percent_cpc.enhanced_cpc_enabled`, `campaign.resource_name`, `campaign.shopping_setting.campaign_priority`, `campaign.shopping_setting.enable_local`, `campaign.shopping_setting.feed_label`, `campaign.shopping_setting.merchant_id`, `campaign.start_date_time`, `campaign.status`, `campaign.target_cpa.cpc_bid_ceiling_micros`, `campaign.target_cpa.cpc_bid_floor_micros`, `campaign.target_cpa.target_cpa_micros`, `campaign.target_cpc.target_cpc_micros`, `campaign.target_cpm.target_frequency_goal.target_count`, `campaign.target_cpm.target_frequency_goal.time_unit`, `campaign.target_impression_share.cpc_bid_ceiling_micros`, `campaign.target_impression_share.location`, `campaign.target_impression_share.location_fraction_micros`, `campaign.target_roas.cpc_bid_ceiling_micros`, `campaign.target_roas.cpc_bid_floor_micros`, `campaign.target_roas.target_roas`, `campaign.target_roas.target_roas_tolerance_percent_millis`, `campaign.target_spend.cpc_bid_ceiling_micros`, `campaign.target_spend.target_spend_micros`, `campaign.tracking_url_template`, `campaign.url_custom_parameters`, `campaign.video_campaign_settings.video_ad_format_control.format_restriction`, `campaign.video_campaign_settings.video_ad_inventory_control.allow_in_feed`, `campaign.video_campaign_settings.video_ad_inventory_control.allow_in_stream`, `campaign.video_campaign_settings.video_ad_inventory_control.allow_non_skippable_in_stream`, `campaign.video_campaign_settings.video_ad_inventory_control.allow_shorts`, `campaign_budget.amount_micros`, `campaign_budget.delivery_method`, `campaign_budget.explicitly_shared`, `campaign_budget.period`, `campaign_budget.total_amount_micros`, `metrics.*`, `metrics.all_conversions`, `metrics.all_conversions_value`, `metrics.auction_insight_search_absolute_top_impression_percentage`, `metrics.auction_insight_search_impression_share`, `metrics.auction_insight_search_outranking_share`, `metrics.auction_insight_search_overlap_rate`, `metrics.auction_insight_search_position_above_rate`, `metrics.auction_insight_search_top_impression_percentage`, `metrics.average_cpc`, `metrics.clicks`, `metrics.content_budget_lost_impression_share`, `metrics.content_impression_share`, `metrics.content_rank_lost_impression_share`, `metrics.conversions`, `metrics.conversions_value`, `metrics.cost_micros`, `metrics.cost_per_conversion`, `metrics.ctr`, `metrics.impressions`, `metrics.search_absolute_top_impression_share`, `metrics.search_budget_lost_impression_share`, `metrics.search_impression_share`, `metrics.search_rank_lost_impression_share`, `metrics.search_top_impression_share`, `segments.ad_network_type`, `segments.auction_insight_domain`, `segments.conversion_action`, `segments.conversion_action_name`, `segments.conversion_lag_bucket`, `segments.date`, `segments.day_of_week`, `segments.device`, `segments.external_conversion_source`, `segments.hour`, `segments.month`, `segments.quarter`, `segments.week`

**Filters used:** `ad_group.id =`, `campaign.advertising_channel_sub_type =`, `campaign.advertising_channel_type =`, `campaign.advertising_channel_type IN`, `campaign.id !=`, `campaign.id =`, `campaign.id IN`, `campaign.name =`, `campaign.name IN`, `campaign.name LIKE`, `campaign.shopping_setting.campaign_priority =`, `campaign.shopping_setting.merchant_id =`, `campaign.status !=`, `campaign.status =`, `campaign.status IN`, `metrics.content_impression_share >=`, `metrics.conversions >`, `metrics.search_impression_share >=`, `segments.conversion_action =`, `segments.date DURING`

**Date field:** `segments.date`

**Ordered by:** `campaign.id ASC`, `campaign.name ASC`, `metrics.auction_insight_search_impression_share DESC`, `metrics.conversions DESC`, `metrics.cost_micros DESC`, `metrics.impressions DESC`

## campaign_asset|ad_group_asset|customer_asset|asset

**Fields:** `ad_group_asset.ad_group`, `ad_group_asset.asset`, `ad_group_asset.field_type`, `ad_group_asset.source`, `ad_group_asset.status`, `asset.call_asset.call_conversion_reporting_state`, `asset.call_asset.country_code`, `asset.call_asset.phone_number`, `asset.callout_asset.callout_text`, `asset.final_mobile_urls`, `asset.final_urls`, `asset.id`, `asset.image_asset.file_size`, `asset.image_asset.full_size.height_pixels`, `asset.image_asset.full_size.url`, `asset.image_asset.full_size.width_pixels`, `asset.lead_form_asset.business_name`, `asset.lead_form_asset.call_to_action_description`, `asset.lead_form_asset.call_to_action_type`, `asset.lead_form_asset.description`, `asset.name`, `asset.policy_summary.approval_status`, `asset.policy_summary.review_status`, `asset.price_asset.language_code`, `asset.price_asset.price_offerings`, `asset.price_asset.price_qualifier`, `asset.price_asset.type`, `asset.promotion_asset.discount_modifier`, `asset.promotion_asset.end_date`, `asset.promotion_asset.money_amount_off.amount_micros`, `asset.promotion_asset.money_amount_off.currency_code`, `asset.promotion_asset.occasion`, `asset.promotion_asset.percent_off`, `asset.promotion_asset.promotion_target`, `asset.promotion_asset.start_date`, `asset.resource_name`, `asset.sitelink_asset.ad_schedule_targets`, `asset.sitelink_asset.description1`, `asset.sitelink_asset.description2`, `asset.sitelink_asset.end_date`, `asset.sitelink_asset.link_text`, `asset.sitelink_asset.start_date`, `asset.structured_snippet_asset.header`, `asset.structured_snippet_asset.values`, `asset.text_asset.text`, `asset.tracking_url_template`, `asset.type`, `asset.url_custom_parameters`, `campaign_asset.asset`, `campaign_asset.campaign`, `campaign_asset.field_type`, `campaign_asset.source`, `campaign_asset.status`, `customer_asset.asset`, `customer_asset.field_type`, `customer_asset.source`, `customer_asset.status`

**Filters used:** `ad_group_asset.ad_group =`, `ad_group_asset.field_type IN`, `ad_group_asset.status !=`, `campaign_asset.campaign =`, `campaign_asset.field_type IN`, `campaign_asset.status !=`, `customer_asset.field_type IN`, `customer_asset.status !=`

## campaign_asset|ad_group_asset|customer_asset|asset_field_type_view

**Fields:** `ad_group.id`, `ad_group.name`, `ad_group_asset.asset`, `ad_group_asset.field_type`, `ad_group_asset.primary_status`, `ad_group_asset.primary_status_details`, `ad_group_asset.primary_status_reasons`, `ad_group_asset.resource_name`, `ad_group_asset.source`, `ad_group_asset.status`, `asset.callout_asset.callout_text`, `asset.final_urls`, `asset.id`, `asset.name`, `asset.sitelink_asset.link_text`, `asset.text_asset.text`, `asset.type`, `asset_field_type_view.field_type`, `asset_field_type_view.resource_name`, `campaign.id`, `campaign.name`, `campaign_asset.asset`, `campaign_asset.field_type`, `campaign_asset.primary_status`, `campaign_asset.primary_status_details`, `campaign_asset.primary_status_reasons`, `campaign_asset.resource_name`, `campaign_asset.source`, `campaign_asset.status`, `customer.currency_code`, `customer.time_zone`, `customer_asset.asset`, `customer_asset.field_type`, `customer_asset.primary_status`, `customer_asset.primary_status_details`, `customer_asset.primary_status_reasons`, `customer_asset.resource_name`, `customer_asset.source`, `customer_asset.status`, `metrics.all_conversions`, `metrics.all_conversions_value`, `metrics.clicks`, `metrics.conversions`, `metrics.conversions_value`, `metrics.cost_micros`, `metrics.impressions`, `segments.asset_interaction_target.interaction_on_this_asset`

**Date field:** `segments.date`

## campaign_bid_modifier

**Fields:** `campaign_bid_modifier.bid_modifier`, `campaign_bid_modifier.campaign`, `campaign_bid_modifier.criterion_id`, `campaign_bid_modifier.interaction_type.type`

**Filters used:** `campaign_bid_modifier.campaign =`

## campaign_budget

**Fields:** `campaign_budget.amount_micros`, `campaign_budget.delivery_method`, `campaign_budget.explicitly_shared`, `campaign_budget.id`, `campaign_budget.name`, `campaign_budget.period`, `campaign_budget.reference_count`, `campaign_budget.resource_name`, `campaign_budget.status`, `campaign_budget.total_amount_micros`, `campaign_budget.type`, `metrics.all_conversions`, `metrics.clicks`, `metrics.conversions`, `metrics.conversions_value`, `metrics.cost_micros`, `metrics.impressions`, `segments.date`, `segments.month`, `segments.quarter`, `segments.week`, `segments.year`

**Filters used:** `campaign_budget.explicitly_shared =`, `campaign_budget.id !=`, `campaign_budget.id =`, `campaign_budget.id IN`, `campaign_budget.name IN`, `campaign_budget.period =`, `campaign_budget.resource_name =`, `campaign_budget.status !=`, `campaign_budget.status IN`, `campaign_budget.type IN`

**Date field:** `segments.date`

**Ordered by:** `campaign_budget.name ASC`

## campaign_conversion_goal

**Fields:** `campaign_conversion_goal.biddable`, `campaign_conversion_goal.campaign`, `campaign_conversion_goal.category`, `campaign_conversion_goal.origin`, `campaign_conversion_goal.resource_name`

**Filters used:** `campaign.status =`, `campaign_conversion_goal.campaign =`

## campaign_criterion

**Fields:** `ad_group.id`, `ad_group.name`, `ad_group_criterion.criterion_id`, `ad_group_criterion.display_name`, `ad_group_criterion.mobile_app_category.mobile_app_category_constant`, `ad_group_criterion.mobile_application.app_id`, `ad_group_criterion.mobile_application.name`, `ad_group_criterion.negative`, `ad_group_criterion.placement.url`, `ad_group_criterion.resource_name`, `ad_group_criterion.status`, `ad_group_criterion.type`, `ad_group_criterion.youtube_channel.channel_id`, `ad_group_criterion.youtube_video.video_id`, `campaign.id`, `campaign.name`, `campaign.resource_name`, `campaign_criterion.*`, `campaign_criterion.bid_modifier`, `campaign_criterion.brand_list.shared_set`, `campaign_criterion.campaign`, `campaign_criterion.combined_audience.combined_audience`, `campaign_criterion.content_label.type`, `campaign_criterion.criterion_id`, `campaign_criterion.custom_affinity.custom_affinity`, `campaign_criterion.custom_audience.custom_audience`, `campaign_criterion.display_name`, `campaign_criterion.income_range.type`, `campaign_criterion.ip_block.ip_address`, `campaign_criterion.language.language_constant`, `campaign_criterion.life_event.life_event_id`, `campaign_criterion.location.geo_target_constant`, `campaign_criterion.mobile_app_category.mobile_app_category_constant`, `campaign_criterion.mobile_application.app_id`, `campaign_criterion.mobile_application.name`, `campaign_criterion.negative`, `campaign_criterion.parental_status.type`, `campaign_criterion.placement.url`, `campaign_criterion.resource_name`, `campaign_criterion.status`, `campaign_criterion.topic.topic_constant`, `campaign_criterion.type`, `campaign_criterion.user_interest.user_interest_category`, `campaign_criterion.user_list.user_list`, `campaign_criterion.youtube_channel.channel_id`, `campaign_criterion.youtube_video.video_id`

**Filters used:** `ad_group.resource_name IN`, `ad_group_criterion.criterion_id IN`, `ad_group_criterion.negative =`, `ad_group_criterion.placement.url LIKE`, `ad_group_criterion.status !=`, `ad_group_criterion.type IN`, `campaign.resource_name IN`, `campaign_criterion.campaign =`, `campaign_criterion.campaign IN`, `campaign_criterion.criterion_id IN`, `campaign_criterion.negative =`, `campaign_criterion.placement.url LIKE`, `campaign_criterion.resource_name IN`, `campaign_criterion.status !=`, `campaign_criterion.type =`, `campaign_criterion.type IN`

**Ordered by:** `campaign.id ASC`, `campaign_criterion.criterion_id ASC`

## campaign_customizer

**Fields:** `campaign.id`, `campaign.name`, `campaign.resource_name`, `campaign_customizer.campaign`, `campaign_customizer.customizer_attribute`, `campaign_customizer.resource_name`, `campaign_customizer.status`, `campaign_customizer.value.string_value`, `campaign_customizer.value.type`, `customizer_attribute.id`, `customizer_attribute.name`, `customizer_attribute.resource_name`, `customizer_attribute.status`, `customizer_attribute.type`

**Filters used:** `campaign.resource_name =`, `campaign_customizer.customizer_attribute =`, `campaign_customizer.status !=`

## campaign_draft

**Fields:** `campaign_draft.base_campaign`, `campaign_draft.draft_campaign`, `campaign_draft.name`, `campaign_draft.resource_name`, `campaign_draft.status`

**Filters used:** `campaign_draft.base_campaign =`, `campaign_draft.resource_name =`, `campaign_draft.status !=`

## campaign_goal_config

**Fields:** `campaign_goal_config.campaign`, `campaign_goal_config.campaign_new_customer_acquisition_settings.target_option`, `campaign_goal_config.campaign_new_customer_acquisition_settings.value_settings_override.additional_high_lifetime_value`, `campaign_goal_config.campaign_new_customer_acquisition_settings.value_settings_override.additional_value`, `campaign_goal_config.campaign_retention_settings.target_option`, `campaign_goal_config.campaign_retention_settings.value_settings_override.additional_high_lifetime_value`, `campaign_goal_config.campaign_retention_settings.value_settings_override.additional_value`, `campaign_goal_config.goal`, `campaign_goal_config.goal_type`, `campaign_goal_config.resource_name`

**Filters used:** `campaign_goal_config.campaign =`

**Ordered by:** `campaign_goal_config.goal_type ASC`

## campaign_group

**Fields:** `campaign_group.id`, `campaign_group.name`, `campaign_group.resource_name`, `campaign_group.status`

**Filters used:** `campaign_group.status !=`, `campaign_group.status =`

**Ordered by:** `campaign_group.name ASC`

## campaign_label

**Fields:** `campaign_label.label`, `label.id`, `label.name`, `label.status`

**Filters used:** `campaign_label.campaign =`

**Ordered by:** `label.name ASC`

## campaign_search_term_insight

**Fields:** `campaign_search_term_insight.category_label`, `metrics.clicks`, `metrics.conversions`, `metrics.impressions`

**Filters used:** `campaign_search_term_insight.campaign_id =`

**Date field:** `segments.date`

**Ordered by:** `metrics.impressions DESC`

## campaign_search_term_view

**Fields:** `campaign_search_term_view.campaign`, `campaign_search_term_view.search_term`, `metrics.average_cpc`, `metrics.clicks`, `metrics.conversions`, `metrics.conversions_value`, `metrics.cost_micros`, `metrics.cost_per_conversion`, `metrics.ctr`, `metrics.impressions`, `segments.search_term_match_type`

**Filters used:** `campaign_search_term_view.campaign =`, `campaign_search_term_view.search_term LIKE`, `metrics.clicks >=`, `metrics.conversions >=`, `metrics.impressions >=`

**Date field:** `segments.date`

**Ordered by:** `metrics.impressions DESC`

## campaign_shared_set

**Fields:** `campaign_shared_set.campaign`, `campaign_shared_set.resource_name`, `campaign_shared_set.shared_set`, `campaign_shared_set.status`, `shared_set.id`, `shared_set.name`, `shared_set.status`, `shared_set.type`

**Filters used:** `campaign_shared_set.campaign =`, `campaign_shared_set.shared_set =`, `campaign_shared_set.status !=`, `campaign_shared_set.status =`, `shared_set.type =`

**Ordered by:** `shared_set.name ASC`

## campaign|campaign_criterion|geo_target_constant

**Fields:** `campaign.geo_target_type_setting.negative_geo_target_type`, `campaign.geo_target_type_setting.positive_geo_target_type`, `campaign.id`, `campaign.name`, `campaign_criterion.bid_modifier`, `campaign_criterion.criterion_id`, `campaign_criterion.display_name`, `campaign_criterion.location.geo_target_constant`, `campaign_criterion.negative`, `campaign_criterion.proximity.*`, `campaign_criterion.resource_name`, `campaign_criterion.status`, `campaign_criterion.type`, `geo_target_constant.canonical_name`, `geo_target_constant.country_code`, `geo_target_constant.id`, `geo_target_constant.name`, `geo_target_constant.target_type`

**Filters used:** `campaign.id =`, `campaign_criterion.campaign =`, `campaign_criterion.status !=`, `campaign_criterion.type IN`, `geo_target_constant.id IN`

**Ordered by:** `campaign_criterion.criterion_id ASC`

## change_event

**Fields:** `change_event.ad_group`, `change_event.campaign`, `change_event.change_date_time`, `change_event.change_resource_name`, `change_event.change_resource_type`, `change_event.changed_fields`, `change_event.client_type`, `change_event.new_resource`, `change_event.old_resource`, `change_event.resource_change_operation`, `change_event.resource_name`, `change_event.user_email`

**Filters used:** `change_event.ad_group =`, `change_event.campaign =`, `change_event.change_date_time BETWEEN`, `change_event.change_resource_type IN`, `change_event.client_type IN`

**Ordered by:** `change_event.change_date_time DESC`

## change_status

**Fields:** `change_status.ad_group`, `change_status.campaign`, `change_status.last_change_date_time`, `change_status.resource_name`, `change_status.resource_status`, `change_status.resource_type`

**Filters used:** `change_status.ad_group =`, `change_status.campaign =`, `change_status.last_change_date_time BETWEEN`, `change_status.resource_status IN`, `change_status.resource_type IN`

**Ordered by:** `change_status.last_change_date_time DESC`

## combined_audience

**Fields:** `combined_audience.description`, `combined_audience.id`, `combined_audience.name`, `combined_audience.resource_name`, `combined_audience.status`

**Filters used:** `combined_audience.status =`

## conversion_action

**Fields:** `conversion_action.attribution_model_settings.attribution_model`, `conversion_action.category`, `conversion_action.click_through_lookback_window_days`, `conversion_action.counting_type`, `conversion_action.id`, `conversion_action.include_in_conversions_metric`, `conversion_action.name`, `conversion_action.origin`, `conversion_action.primary_for_goal`, `conversion_action.status`, `conversion_action.tag_snippets`, `conversion_action.type`, `conversion_action.value_settings.always_use_default_value`, `conversion_action.value_settings.default_currency_code`, `conversion_action.value_settings.default_value`, `conversion_action.view_through_lookback_window_days`

**Filters used:** `conversion_action.category =`, `conversion_action.id =`, `conversion_action.primary_for_goal =`, `conversion_action.status =`

## conversion_custom_variable

**Fields:** `conversion_custom_variable.id`, `conversion_custom_variable.name`, `conversion_custom_variable.owner_customer`, `conversion_custom_variable.resource_name`, `conversion_custom_variable.status`, `conversion_custom_variable.tag`

## conversion_goal_campaign_config

**Fields:** `conversion_goal_campaign_config.campaign`, `conversion_goal_campaign_config.custom_conversion_goal`, `conversion_goal_campaign_config.goal_config_level`, `conversion_goal_campaign_config.resource_name`

**Filters used:** `conversion_goal_campaign_config.campaign =`, `conversion_goal_campaign_config.goal_config_level =`

**Ordered by:** `conversion_goal_campaign_config.goal_config_level ASC`

## conversion_value_rule

**Fields:** `conversion_value_rule.action.operation`, `conversion_value_rule.action.value`, `conversion_value_rule.id`, `conversion_value_rule.owner_customer`, `conversion_value_rule.resource_name`, `conversion_value_rule.status`

## conversion_value_rule_set

**Fields:** `conversion_value_rule_set.attachment_type`, `conversion_value_rule_set.campaign`, `conversion_value_rule_set.conversion_action_categories`, `conversion_value_rule_set.conversion_value_rules`, `conversion_value_rule_set.dimensions`, `conversion_value_rule_set.id`, `conversion_value_rule_set.owner_customer`, `conversion_value_rule_set.resource_name`, `conversion_value_rule_set.status`

**Filters used:** `conversion_value_rule_set.campaign =`, `conversion_value_rule_set.status =`

**Ordered by:** `conversion_value_rule_set.id DESC`

## custom_audience

**Fields:** `custom_audience.description`, `custom_audience.id`, `custom_audience.members`, `custom_audience.name`, `custom_audience.resource_name`, `custom_audience.status`, `custom_audience.type`

**Filters used:** `custom_audience.id =`, `custom_audience.status =`

## custom_interest

**Fields:** `custom_interest.description`, `custom_interest.id`, `custom_interest.members`, `custom_interest.name`, `custom_interest.resource_name`, `custom_interest.status`, `custom_interest.type`

**Filters used:** `custom_interest.id =`, `custom_interest.status =`, `custom_interest.type =`

**Ordered by:** `custom_interest.name ASC`

## customer

**Fields:** `customer.auto_tagging_enabled`, `customer.conversion_tracking_setting.conversion_tracking_status`, `customer.conversion_tracking_setting.google_ads_conversion_customer`, `customer.currency_code`, `customer.descriptive_name`, `customer.final_url_suffix`, `customer.has_partners_badge`, `customer.id`, `customer.manager`, `customer.optimization_score`, `customer.optimization_score_weight`, `customer.remarketing_setting.google_global_site_tag`, `customer.status`, `customer.test_account`, `customer.time_zone`, `customer.tracking_url_template`, `customer.video_brand_safety_suitability`, `metrics.cost_micros`, `segments.date`

**Date field:** `segments.date`

## customer_asset_set

**Fields:** `customer_asset_set.asset_set`, `customer_asset_set.resource_name`, `customer_asset_set.status`

**Filters used:** `customer_asset_set.asset_set =`, `customer_asset_set.status =`

**Ordered by:** `customer_asset_set.status ASC`

## customer_conversion_goal

**Fields:** `customer_conversion_goal.biddable`, `customer_conversion_goal.category`, `customer_conversion_goal.origin`

## customer_customizer

**Fields:** `customer_customizer.customizer_attribute`, `customer_customizer.resource_name`, `customer_customizer.status`, `customer_customizer.value.string_value`, `customer_customizer.value.type`, `customizer_attribute.id`, `customizer_attribute.name`, `customizer_attribute.resource_name`, `customizer_attribute.status`, `customizer_attribute.type`

**Filters used:** `customer_customizer.customizer_attribute =`, `customer_customizer.status !=`

## customer_label

**Fields:** `customer_label.customer`, `customer_label.label`, `customer_label.resource_name`

**Filters used:** `customer_label.label =`

## customer_sk_ad_network_conversion_value_schema

**Fields:** `customer_sk_ad_network_conversion_value_schema.resource_name`, `customer_sk_ad_network_conversion_value_schema.schema.app_id`, `customer_sk_ad_network_conversion_value_schema.schema.measurement_window_hours`

**Filters used:** `customer_sk_ad_network_conversion_value_schema.resource_name =`

## customer|campaign

**Fields:** `campaign.id`, `campaign.name`, `campaign.optimization_score`, `customer.descriptive_name`, `customer.id`, `customer.optimization_score`, `metrics.all_conversions`, `metrics.all_conversions_value`, `metrics.clicks`, `metrics.conversions`, `metrics.conversions_value`, `metrics.cost_per_conversion`, `segments.conversion_action`, `segments.conversion_action_category`, `segments.conversion_action_name`

**Filters used:** `campaign.id IN`

**Date field:** `segments.date`

## customer|campaign|ad_group

**Fields:** `ad_group.id`, `ad_group.name`, `campaign.id`, `campaign.name`, `metrics.auction_insight_search_absolute_top_impression_percentage`, `metrics.auction_insight_search_impression_share`, `metrics.auction_insight_search_outranking_share`, `metrics.auction_insight_search_overlap_rate`, `metrics.auction_insight_search_position_above_rate`, `metrics.auction_insight_search_top_impression_percentage`, `segments.auction_insight_domain`

**Filters used:** `ad_group.id IN`, `campaign.id IN`

**Date field:** `segments.date`

**Ordered by:** `metrics.auction_insight_search_impression_share DESC`

## customizer_attribute

**Fields:** `customizer_attribute.id`, `customizer_attribute.name`, `customizer_attribute.resource_name`, `customizer_attribute.status`, `customizer_attribute.type`

**Filters used:** `customizer_attribute.name =`, `customizer_attribute.resource_name =`, `customizer_attribute.status !=`

## final_url_expansion_asset_view

**Fields:** `final_url_expansion_asset_view.ad_group`, `final_url_expansion_asset_view.asset`, `final_url_expansion_asset_view.asset_group`, `final_url_expansion_asset_view.campaign`, `final_url_expansion_asset_view.field_type`, `final_url_expansion_asset_view.final_url`, `final_url_expansion_asset_view.resource_name`, `final_url_expansion_asset_view.status`, `metrics.conversions`, `metrics.conversions_value`, `metrics.impressions`

**Filters used:** `final_url_expansion_asset_view.ad_group =`, `final_url_expansion_asset_view.asset =`, `final_url_expansion_asset_view.asset_group =`, `final_url_expansion_asset_view.campaign =`, `final_url_expansion_asset_view.status =`, `metrics.conversions >=`, `metrics.impressions >=`

**Date field:** `segments.date`

**Ordered by:** `metrics.impressions DESC`

## geo_target_constant

**Fields:** `geo_target_constant.canonical_name`, `geo_target_constant.country_code`, `geo_target_constant.id`, `geo_target_constant.name`, `geo_target_constant.resource_name`, `geo_target_constant.status`, `geo_target_constant.target_type`

**Filters used:** `geo_target_constant.id IN`

## geographic_view

**Fields:** `campaign.id`, `campaign.name`, `metrics.average_cpc`, `metrics.clicks`, `metrics.conversions`, `metrics.conversions_value`, `metrics.cost_micros`, `metrics.cost_per_conversion`, `metrics.ctr`, `metrics.impressions`, `segments.geo_target_city`, `segments.geo_target_country`, `segments.geo_target_metro`, `segments.geo_target_most_specific_location`, `segments.geo_target_region`

**Filters used:** `campaign.id =`, `metrics.clicks >=`, `metrics.impressions >=`

**Date field:** `segments.date`

**Ordered by:** `metrics.impressions DESC`

## goal

**Fields:** `goal.goal_id`, `goal.goal_type`, `goal.new_customer_acquisition_goal_settings.value_settings.additional_high_lifetime_value`, `goal.new_customer_acquisition_goal_settings.value_settings.additional_value`, `goal.optimization_eligibility`, `goal.owner_customer`, `goal.resource_name`, `goal.retention_goal_settings.value_settings.additional_high_lifetime_value`, `goal.retention_goal_settings.value_settings.additional_value`

**Filters used:** `goal.goal_type =`, `goal.optimization_eligibility =`

**Ordered by:** `goal.goal_id ASC`

## group_placement_view

**Fields:** `ad_group.id`, `ad_group.name`, `campaign.id`, `campaign.name`, `group_placement_view.display_name`, `group_placement_view.placement`, `group_placement_view.placement_type`, `group_placement_view.target_url`, `metrics.clicks`, `metrics.conversions`, `metrics.cost_micros`, `metrics.ctr`, `metrics.impressions`

**Filters used:** `ad_group.id =`, `campaign.id =`, `campaign.id IN`, `metrics.impressions >=`, `segments.date <=`, `segments.date >=`

**Date field:** `segments.date`

**Ordered by:** `metrics.impressions DESC`

## keyword_plan_campaign_keyword

**Fields:** `keyword_plan_campaign_keyword.id`, `keyword_plan_campaign_keyword.keyword_plan_campaign`, `keyword_plan_campaign_keyword.match_type`, `keyword_plan_campaign_keyword.negative`, `keyword_plan_campaign_keyword.resource_name`, `keyword_plan_campaign_keyword.text`

**Filters used:** `keyword_plan_campaign_keyword.keyword_plan_campaign =`

## keyword_view

**Fields:** `ad_group.id`, `ad_group.name`, `ad_group_criterion.criterion_id`, `ad_group_criterion.keyword.match_type`, `ad_group_criterion.keyword.text`, `ad_group_criterion.negative`, `ad_group_criterion.quality_info.creative_quality_score`, `ad_group_criterion.quality_info.post_click_quality_score`, `ad_group_criterion.quality_info.quality_score`, `ad_group_criterion.quality_info.search_predicted_ctr`, `ad_group_criterion.status`, `campaign.id`, `campaign.name`, `metrics.average_cpc`, `metrics.clicks`, `metrics.conversions`, `metrics.conversions_value`, `metrics.cost_micros`, `metrics.cost_per_conversion`, `metrics.ctr`, `metrics.impressions`, `metrics.search_absolute_top_impression_share`, `metrics.search_impression_share`, `metrics.search_top_impression_share`

**Filters used:** `ad_group.id =`, `ad_group_criterion.negative =`, `ad_group_criterion.status =`, `ad_group_criterion.status IN`, `ad_group_criterion.type =`, `campaign.id =`, `metrics.clicks >=`, `metrics.impressions >=`

**Date field:** `segments.date`

**Ordered by:** `metrics.cost_micros DESC`

## label

**Fields:** `label.id`, `label.name`, `label.resource_name`, `label.status`, `label.text_label.background_color`, `label.text_label.description`

**Filters used:** `label.id =`, `label.name LIKE`, `label.status =`

**Ordered by:** `label.name ASC`

## landing_page_view

**Fields:** `landing_page_view.unexpanded_final_url`, `metrics.average_cpc`, `metrics.clicks`, `metrics.conversions`, `metrics.conversions_value`, `metrics.cost_micros`, `metrics.cost_per_conversion`, `metrics.ctr`, `metrics.impressions`, `metrics.mobile_friendly_clicks_percentage`, `metrics.speed_score`

**Filters used:** `landing_page_view.unexpanded_final_url LIKE`, `metrics.clicks >=`, `metrics.impressions >=`

**Date field:** `segments.date`

**Ordered by:** `metrics.clicks DESC`, `metrics.impressions DESC`

## lift_measurement_config

**Fields:** `lift_measurement_config.conversion_actions`, `lift_measurement_config.conversion_lift_holdback_ratio_micros`, `lift_measurement_config.lift_measurement_config_id`, `lift_measurement_config.name`, `lift_measurement_config.resource_name`, `lift_measurement_config.survey_language`, `metrics.absolute_brand_lift`, `metrics.incremental_conversions`, `metrics.relative_brand_lift`

**Filters used:** `lift_measurement_config.lift_measurement_config_id =`

## matched_location_interest_view

**Fields:** `matched_location_interest_view.resource_name`, `metrics.average_cpc`, `metrics.clicks`, `metrics.conversions`, `metrics.conversions_value`, `metrics.cost_micros`, `metrics.cost_per_conversion`, `metrics.ctr`, `metrics.impressions`, `segments.geo_target_*`

**Filters used:** `metrics.clicks >=`, `metrics.conversions >=`, `metrics.impressions >=`

**Date field:** `segments.date`

**Ordered by:** `metrics.impressions DESC`

## per_store_view

**Fields:** `metrics.all_conversions_from_location_asset_click_to_call`, `metrics.all_conversions_from_location_asset_directions`, `metrics.all_conversions_from_location_asset_menu`, `metrics.all_conversions_from_location_asset_order`, `metrics.all_conversions_from_location_asset_other_engagement`, `metrics.all_conversions_from_location_asset_store_visits`, `metrics.all_conversions_from_location_asset_website`, `metrics.eligible_impressions_from_location_asset_store_reach`, `metrics.view_through_conversions_from_location_asset_click_to_call`, `metrics.view_through_conversions_from_location_asset_directions`, `metrics.view_through_conversions_from_location_asset_menu`, `metrics.view_through_conversions_from_location_asset_order`, `metrics.view_through_conversions_from_location_asset_other_engagement`, `metrics.view_through_conversions_from_location_asset_store_visits`, `metrics.view_through_conversions_from_location_asset_website`, `per_store_view.address1`, `per_store_view.address2`, `per_store_view.business_name`, `per_store_view.city`, `per_store_view.country_code`, `per_store_view.phone_number`, `per_store_view.place_id`, `per_store_view.postal_code`, `per_store_view.province`, `per_store_view.resource_name`

**Filters used:** `metrics.all_conversions_from_location_asset_store_visits >=`, `metrics.eligible_impressions_from_location_asset_store_reach >=`, `per_store_view.place_id =`

**Date field:** `segments.date`

**Ordered by:** `metrics.eligible_impressions_from_location_asset_store_reach DESC`

## performance_max_placement_view

**Fields:** `metrics.impressions`, `performance_max_placement_view.display_name`, `performance_max_placement_view.placement`, `performance_max_placement_view.placement_type`, `performance_max_placement_view.target_url`

**Filters used:** `metrics.impressions >=`, `performance_max_placement_view.display_name LIKE`, `performance_max_placement_view.placement_type =`, `performance_max_placement_view.target_url LIKE`

**Date field:** `segments.date`

**Ordered by:** `metrics.impressions DESC`

## product_link

**Fields:** `product_link.advertising_partner.customer`, `product_link.advertising_partner_properties.allowed_domain`, `product_link.data_partner.data_partner_id`, `product_link.google_ads.customer`, `product_link.merchant_center.merchant_center_id`, `product_link.product_link_id`, `product_link.resource_name`, `product_link.type`

**Ordered by:** `product_link.product_link_id ASC`

## product_link_invitation

**Fields:** `product_link_invitation.advertising_partner.customer`, `product_link_invitation.advertising_partner_properties.allowed_domain`, `product_link_invitation.hotel_center.hotel_center_id`, `product_link_invitation.merchant_center.merchant_center_id`, `product_link_invitation.product_link_invitation_id`, `product_link_invitation.resource_name`, `product_link_invitation.status`, `product_link_invitation.type`

**Filters used:** `product_link_invitation.advertising_partner.customer =`, `product_link_invitation.hotel_center.hotel_center_id =`, `product_link_invitation.merchant_center.merchant_center_id =`, `product_link_invitation.product_link_invitation_id =`, `product_link_invitation.resource_name =`, `product_link_invitation.status =`, `product_link_invitation.type =`

**Ordered by:** `product_link_invitation.product_link_invitation_id DESC`

## recommendation

**Fields:** `ad_group.name`, `campaign.name`, `campaign_budget.name`, `customer.currency_code`, `recommendation.ad_group`, `recommendation.call_asset_recommendation`, `recommendation.callout_asset_recommendation`, `recommendation.campaign`, `recommendation.campaign_budget`, `recommendation.campaign_budget_recommendation`, `recommendation.campaign_specific_app_goal_recommendation`, `recommendation.campaigns`, `recommendation.custom_audience_opt_in_recommendation`, `recommendation.dismissed`, `recommendation.display_expansion_opt_in_recommendation`, `recommendation.dynamic_image_extension_opt_in_recommendation`, `recommendation.enhanced_cpc_opt_in_recommendation`, `recommendation.forecasting_campaign_budget_recommendation`, `recommendation.forecasting_set_target_cpa_recommendation`, `recommendation.forecasting_set_target_roas_recommendation`, `recommendation.impact`, `recommendation.improve_demand_gen_ad_strength_recommendation`, `recommendation.improve_google_tag_coverage_recommendation`, `recommendation.improve_performance_max_ad_strength_recommendation`, `recommendation.keyword_match_type_recommendation`, `recommendation.keyword_recommendation`, `recommendation.lead_form_asset_recommendation`, `recommendation.lower_target_roas_performance_bid_too_low_recommendation`, `recommendation.lower_target_roas_recommendation`, `recommendation.marginal_roi_campaign_budget_recommendation`, `recommendation.maximize_clicks_opt_in_recommendation`, `recommendation.maximize_conversion_value_opt_in_recommendation`, `recommendation.maximize_conversions_opt_in_recommendation`, `recommendation.migrate_dynamic_search_ads_campaign_to_performance_max_recommendation`, `recommendation.move_unused_budget_recommendation`, `recommendation.optimize_ad_rotation_recommendation`, `recommendation.performance_max_final_url_opt_in_recommendation`, `recommendation.performance_max_opt_in_recommendation`, `recommendation.raise_target_cpa_bid_too_low_recommendation`, `recommendation.raise_target_cpa_performance_bid_too_low_recommendation`, `recommendation.raise_target_cpa_recommendation`, `recommendation.refresh_customer_match_list_recommendation`, `recommendation.resource_name`, `recommendation.responsive_search_ad_asset_recommendation`, `recommendation.responsive_search_ad_improve_ad_strength_recommendation`, `recommendation.responsive_search_ad_recommendation`, `recommendation.search_partners_opt_in_recommendation`, `recommendation.set_target_cpa_recommendation`, `recommendation.set_target_roas_recommendation`, `recommendation.shopping_add_age_group_recommendation`, `recommendation.shopping_add_color_recommendation`, `recommendation.shopping_add_gender_recommendation`, `recommendation.shopping_add_gtin_recommendation`, `recommendation.shopping_add_more_identifiers_recommendation`, `recommendation.shopping_add_products_to_campaign_recommendation`, `recommendation.shopping_add_size_recommendation`, `recommendation.shopping_fix_disapproved_products_recommendation`, `recommendation.shopping_fix_merchant_center_account_suspension_warning_recommendation`, `recommendation.shopping_fix_suspended_merchant_center_account_recommendation`, `recommendation.shopping_migrate_regular_shopping_campaign_offers_to_performance_max_recommendation`, `recommendation.shopping_target_all_offers_recommendation`, `recommendation.sitelink_asset_recommendation`, `recommendation.target_cpa_opt_in_recommendation`, `recommendation.target_roas_opt_in_recommendation`, `recommendation.text_ad_recommendation`, `recommendation.type`, `recommendation.upgrade_local_campaign_to_performance_max_recommendation`, `recommendation.upgrade_smart_shopping_campaign_to_performance_max_recommendation`, `recommendation.use_broad_match_keyword_recommendation`

**Filters used:** `recommendation.campaign =`, `recommendation.dismissed =`, `recommendation.resource_name =`, `recommendation.type IN`

**Ordered by:** `recommendation.type ASC`

## recommendation_subscription

**Fields:** `recommendation_subscription.create_date_time`, `recommendation_subscription.modify_date_time`, `recommendation_subscription.resource_name`, `recommendation_subscription.status`, `recommendation_subscription.type`

**Ordered by:** `recommendation_subscription.type ASC`

## search_term_view

**Fields:** `metrics.average_cpc`, `metrics.clicks`, `metrics.conversions`, `metrics.conversions_value`, `metrics.cost_micros`, `metrics.cost_per_conversion`, `metrics.ctr`, `metrics.impressions`, `search_term_view.ad_group`, `search_term_view.search_term`, `search_term_view.status`, `segments.keyword.ad_group_criterion`, `segments.keyword.info.text`, `segments.search_term_match_type`

**Filters used:** `metrics.clicks >=`, `metrics.conversions >=`, `metrics.impressions >=`, `search_term_view.ad_group =`, `search_term_view.ad_group IN`, `search_term_view.search_term LIKE`, `segments.date DURING`

**Date field:** `segments.date`

**Ordered by:** `metrics.clicks DESC`, `metrics.impressions DESC`

## shared_criterion

**Fields:** `shared_criterion.brand.display_name`, `shared_criterion.brand.entity_id`, `shared_criterion.brand.primary_url`, `shared_criterion.brand.rejection_reason`, `shared_criterion.brand.status`, `shared_criterion.criterion_id`, `shared_criterion.keyword.match_type`, `shared_criterion.keyword.text`, `shared_criterion.mobile_app_category.mobile_app_category_constant`, `shared_criterion.mobile_application.app_id`, `shared_criterion.mobile_application.name`, `shared_criterion.placement.url`, `shared_criterion.resource_name`, `shared_criterion.type`, `shared_criterion.webpage.conditions`, `shared_criterion.webpage.coverage_percentage`, `shared_criterion.webpage.criterion_name`, `shared_criterion.webpage.sample.sample_urls`, `shared_criterion.youtube_channel.channel_id`, `shared_criterion.youtube_video.video_id`

**Filters used:** `shared_criterion.shared_set =`, `shared_criterion.type =`

**Ordered by:** `shared_criterion.criterion_id ASC`

## shared_set

**Fields:** `shared_set.id`, `shared_set.member_count`, `shared_set.name`, `shared_set.reference_count`, `shared_set.resource_name`, `shared_set.status`, `shared_set.type`

**Filters used:** `shared_set.status !=`, `shared_set.status =`, `shared_set.type =`, `shared_set.type IN`

**Ordered by:** `shared_set.name ASC`

## smart_campaign_setting

**Fields:** `smart_campaign_setting.advertising_language_code`, `smart_campaign_setting.business_name`, `smart_campaign_setting.final_url`

**Filters used:** `smart_campaign_setting.campaign =`

## third_party_app_analytics_link

**Fields:** `third_party_app_analytics_link.resource_name`, `third_party_app_analytics_link.shareable_link_id`

**Filters used:** `third_party_app_analytics_link.shareable_link_id =`

**Ordered by:** `third_party_app_analytics_link.shareable_link_id DESC`

## user_list

**Fields:** `user_list.description`, `user_list.eligible_for_display`, `user_list.eligible_for_search`, `user_list.id`, `user_list.membership_life_span`, `user_list.membership_status`, `user_list.name`, `user_list.size_for_display`, `user_list.size_for_search`, `user_list.type`

**Filters used:** `user_list.membership_status =`, `user_list.type =`

**Ordered by:** `user_list.name ASC`

## user_list_customer_type

**Fields:** `user_list_customer_type.customer_type_category`, `user_list_customer_type.resource_name`, `user_list_customer_type.user_list`

**Filters used:** `user_list_customer_type.customer_type_category =`, `user_list_customer_type.user_list =`

**Ordered by:** `user_list_customer_type.user_list ASC`

## user_list|custom_audience|combined_audience|detailed_demographic|user_interest

**Fields:** `combined_audience.description`, `combined_audience.id`, `combined_audience.name`, `combined_audience.status`, `custom_audience.description`, `custom_audience.id`, `custom_audience.name`, `custom_audience.status`, `detailed_demographic.id`, `detailed_demographic.name`, `user_interest.name`, `user_interest.taxonomy_type`, `user_interest.user_interest_id`, `user_list.description`, `user_list.id`, `user_list.membership_status`, `user_list.name`, `user_list.size_for_display`, `user_list.size_for_search`

**Filters used:** `user_interest.taxonomy_type IN`

**Ordered by:** `combined_audience.name ASC`, `custom_audience.name ASC`, `detailed_demographic.name ASC`, `user_interest.name ASC`, `user_list.name ASC`


view: yoda_e2e_loyalty__fact_store_profile_daily {
  sql_table_name: public_yoda_e2e_loyalty.fact_store_profile_daily ;;

  dimension_group: ref_time {
    type: time
    sql: ${TABLE}.ref_time ;;
    description: "TODO: Update Column ref_time Information"
    datatype: datetime
    timeframes: [
      raw,
      time,
      hour,
      date,
      week,
      month,
      quarter,
      year,
    ]
  }

  dimension: app_key {
    type: string
    sql: ${TABLE}.app_key ;;
    description: "TODO: Update Column app_key Information"
  }

  dimension: count_campaigns {
    type: number
    sql: ${TABLE}.count_campaigns ;;
    description: "TODO: Update Column count_campaigns Information"
  }

  dimension: sum_active_campaigns {
    type: number
    sql: ${TABLE}.sum_active_campaigns ;;
    description: "TODO: Update Column sum_active_campaigns Information"
  }

  dimension: count_redemptions {
    type: number
    sql: ${TABLE}.count_redemptions ;;
    description: "TODO: Update Column count_redemptions Information"
  }

  dimension: sum_points_redeemed {
    type: number
    sql: ${TABLE}.sum_points_redeemed ;;
    description: "TODO: Update Column sum_points_redeemed Information"
  }

  dimension: count_purchases {
    type: number
    sql: ${TABLE}.count_purchases ;;
    description: "TODO: Update Column count_purchases Information"
  }

  dimension: primary_key {
    primary_key: yes
    sql: CONCAT(${TABLE}.app_key,${TABLE}.ref_time) ;;
    description: "auto generated compound key from the columns:app_key, ref_time"
  }
}
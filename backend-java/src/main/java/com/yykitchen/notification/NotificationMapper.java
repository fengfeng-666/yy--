package com.yykitchen.notification;

import java.util.*;
import org.apache.ibatis.annotations.*;

@Mapper
public interface NotificationMapper {
  @Select(
      value =
          "INSERT INTO wechat_subscriptions(user_id,event_type,available_count) VALUES(#{user},#{event},1) ON CONFLICT(user_id,event_type) DO UPDATE SET available_count=wechat_subscriptions.available_count+1,updated_at=now() RETURNING available_count",
      affectData = true)
  int grant(@Param("user") long user, @Param("event") String event);

  @Update(
      "UPDATE wechat_subscriptions SET available_count=available_count-1,updated_at=now() WHERE user_id=#{user} AND event_type=#{event} AND available_count>0")
  int consume(@Param("user") long user, @Param("event") String event);

  @Insert(
      "INSERT INTO wechat_notifications(recipient_id,meal_order_id,event_type,template_id,page,payload,status) VALUES(#{recipient},#{order},#{event},#{template},'pages/orders/index',CAST(#{payload} AS json),'pending')")
  void enqueue(
      @Param("recipient") long recipient,
      @Param("order") long order,
      @Param("event") String event,
      @Param("template") String template,
      @Param("payload") String payload);

  @Select(
      value =
          "WITH selected AS (SELECT id FROM wechat_notifications WHERE status='pending' ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1), claimed AS (UPDATE wechat_notifications SET status='sending',attempt_count=attempt_count+1,updated_at=now() WHERE id IN (SELECT id FROM selected) RETURNING *) SELECT row_to_json(claimed)::text FROM claimed",
      affectData = true)
  String claim();

  @Update(
      "UPDATE wechat_notifications SET status=#{status},error_message=#{error},sent_at=CASE WHEN #{status}='sent' THEN now() ELSE sent_at END,updated_at=now() WHERE id=#{id}")
  void finish(@Param("id") long id, @Param("status") String status, @Param("error") String error);

  @Update(
      "UPDATE wechat_notifications SET status='failed',error_message='Delivery interrupted; inspect before retrying',updated_at=now() WHERE status='sending' AND updated_at<now()-interval '5 minutes'")
  void interrupted();
}

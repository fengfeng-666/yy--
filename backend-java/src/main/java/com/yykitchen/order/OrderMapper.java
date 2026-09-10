package com.yykitchen.order;

import java.util.*;
import org.apache.ibatis.annotations.*;

@Mapper
public interface OrderMapper {
  List<String> headers(
      @Param("family") long family,
      @Param("user") long user,
      @Param("id") Long id,
      @Param("role") String role,
      @Param("status") String status,
      @Param("history") boolean history);

  List<String> items(@Param("family") long family, @Param("ids") List<Long> ids);

  @Select(
      "SELECT row_to_json(o)::text FROM meal_orders o WHERE family_id=#{family} AND requester_id=#{user} AND request_id=#{request}")
  String existing(
      @Param("family") long family, @Param("user") long user, @Param("request") String request);

  @Select(
      value =
          "INSERT INTO meal_orders(family_id,requester_id,cook_id,status,planned_date,planned_time,note,request_id,request_hash) VALUES(#{family},#{user},#{p.cook_id},'pending',#{p.planned_date},#{p.planned_time},#{p.note},#{p.requestId},#{hash}) ON CONFLICT(family_id,requester_id,request_id) DO NOTHING RETURNING id",
      affectData = true)
  Long create(
      @Param("family") long family,
      @Param("user") long user,
      @Param("p") OrderRequest p,
      @Param("hash") String hash);

  void addItems(@Param("order") long order, @Param("items") List<OrderRequest.Item> items);

  @Insert(
      "INSERT INTO order_status_logs(meal_order_id,from_status,to_status,operator_id,note) VALUES(#{order},#{from},#{to},#{user},#{note})")
  void log(
      @Param("order") long order,
      @Param("from") String from,
      @Param("to") String to,
      @Param("user") long user,
      @Param("note") String note);

  @Update(
      "UPDATE meal_orders SET status='accepted',accepted_at=now(),updated_at=now() WHERE id=#{id} AND family_id=#{family} AND cook_id=#{user} AND status='pending'")
  int accept(@Param("family") long family, @Param("id") long id, @Param("user") long user);

  @Insert(
      "INSERT INTO meal_reviews(meal_order_id,reviewer_id,rating,content) VALUES(#{id},#{user},#{rating},#{content}) ON CONFLICT(meal_order_id) DO NOTHING")
  int review(
      @Param("id") long id,
      @Param("user") long user,
      @Param("rating") int rating,
      @Param("content") String content);
}

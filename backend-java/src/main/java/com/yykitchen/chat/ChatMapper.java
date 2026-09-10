package com.yykitchen.chat;

import java.util.List;
import org.apache.ibatis.annotations.*;

@Mapper
public interface ChatMapper {
  List<String> list(
      @Param("family") long family,
      @Param("before") Long before,
      @Param("after") Long after,
      @Param("limit") int limit);

  @Select(
      "SELECT (to_jsonb(m)||jsonb_build_object('sender',to_jsonb(u)))::text FROM chat_messages m JOIN yy_user_profiles u ON u.id=m.sender_id WHERE m.family_id=#{family} AND m.id=#{id}")
  String get(@Param("family") long family, @Param("id") long id);

  @Select(
      value =
          "INSERT INTO chat_messages(family_id,sender_id,content) VALUES(#{family},#{user},#{content}) RETURNING id",
      affectData = true)
  long create(
      @Param("family") long family, @Param("user") long user, @Param("content") String content);

  @Select(
      "SELECT count(*) FROM chat_messages WHERE family_id=#{family} AND sender_id!=#{user} AND id>COALESCE((SELECT last_read_message_id FROM chat_read_states WHERE family_id=#{family} AND user_id=#{user}),0)")
  int unread(@Param("family") long family, @Param("user") long user);

  @Insert(
      "INSERT INTO chat_read_states(family_id,user_id,last_read_message_id) VALUES(#{family},#{user},#{id}) ON CONFLICT(family_id,user_id) DO UPDATE SET last_read_message_id=GREATEST(chat_read_states.last_read_message_id,EXCLUDED.last_read_message_id),updated_at=now()")
  void read(@Param("family") long family, @Param("user") long user, @Param("id") long id);
}

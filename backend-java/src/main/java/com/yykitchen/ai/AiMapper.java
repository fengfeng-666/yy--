package com.yykitchen.ai;

import java.util.List;
import org.apache.ibatis.annotations.*;

@Mapper
public interface AiMapper {
  @Select(
      "SELECT row_to_json(c)::text FROM ai_chat_conversations c WHERE family_id=#{family} AND user_id=#{user} AND id=#{id}")
  String conversation(@Param("family") long family, @Param("user") long user, @Param("id") long id);

  @Select(
      "SELECT (to_jsonb(c)||jsonb_build_object('last_message_preview',(SELECT left(content,60) FROM ai_chat_messages WHERE conversation_id=c.id ORDER BY id DESC LIMIT 1),'last_message_at',(SELECT created_at FROM ai_chat_messages WHERE conversation_id=c.id ORDER BY id DESC LIMIT 1)))::text FROM ai_chat_conversations c WHERE family_id=#{family} AND user_id=#{user} ORDER BY updated_at DESC,id DESC")
  List<String> conversations(@Param("family") long family, @Param("user") long user);

  @Select(
      value =
          "INSERT INTO ai_chat_conversations(family_id,user_id,title) VALUES(#{family},#{user},#{title}) RETURNING id",
      affectData = true)
  long createConversation(
      @Param("family") long family, @Param("user") long user, @Param("title") String title);

  @Delete(
      "DELETE FROM ai_chat_conversations WHERE family_id=#{family} AND user_id=#{user} AND id=#{id}")
  int delete(@Param("family") long family, @Param("user") long user, @Param("id") long id);

  @Select(
      value =
          "INSERT INTO ai_chat_messages(family_id,user_id,conversation_id,role,content,message_kind,metadata_json) VALUES(#{family},#{user},#{conversation},#{role},#{content},#{kind},CAST(#{metadata} AS json)) RETURNING id",
      affectData = true)
  long createMessage(
      @Param("family") long family,
      @Param("user") long user,
      @Param("conversation") long conversation,
      @Param("role") String role,
      @Param("content") String content,
      @Param("kind") String kind,
      @Param("metadata") String metadata);

  @Select(
      "SELECT row_to_json(m)::text FROM ai_chat_messages m WHERE family_id=#{family} AND user_id=#{user} AND id=#{id}")
  String message(@Param("family") long family, @Param("user") long user, @Param("id") long id);

  List<String> messages(
      @Param("family") long family,
      @Param("user") long user,
      @Param("conversation") long conversation,
      @Param("before") Long before,
      @Param("limit") int limit);

  @Update("UPDATE ai_chat_conversations SET updated_at=now() WHERE id=#{id}")
  void touch(long id);

  @Insert(
      "INSERT INTO fridge_image_analyses(family_id,user_id,image_url,recognized_ingredients_json,raw_model_output) VALUES(#{family},#{user},#{image},CAST(#{ingredients} AS json),#{raw})")
  void imageAnalysis(
      @Param("family") long family,
      @Param("user") long user,
      @Param("image") String image,
      @Param("ingredients") String ingredients,
      @Param("raw") String raw);
}

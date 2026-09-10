package com.yykitchen.identity;

import java.util.*;
import org.apache.ibatis.annotations.*;

@Mapper
public interface IdentityMapper {
  @Select("SELECT row_to_json(u)::text FROM users u WHERE id=#{id}")
  String user(long id);

  @Select("SELECT row_to_json(u)::text FROM users u WHERE username=#{username}")
  String byUsername(String username);

  @Select("SELECT row_to_json(u)::text FROM users u WHERE wechat_openid=#{openid}")
  String byOpenid(String openid);

  @Select("SELECT row_to_json(u)::text FROM yy_user_profiles u WHERE id=#{id}")
  String profile(long id);

  @Select("SELECT id FROM users WHERE id=#{id} FOR UPDATE")
  Long lockUser(long id);

  @Select(
      value =
          "INSERT INTO users(username,nickname,password_hash,wechat_openid,wechat_unionid) VALUES(#{username},#{nickname},#{hash},#{openid},#{unionid}) RETURNING id",
      affectData = true)
  long createUser(
      @Param("username") String username,
      @Param("nickname") String nickname,
      @Param("hash") String hash,
      @Param("openid") String openid,
      @Param("unionid") String unionid);

  @Update("UPDATE users SET nickname=#{nickname}, updated_at=now() WHERE id=#{id}")
  void nickname(@Param("id") long id, @Param("nickname") String nickname);

  @Update(
      "UPDATE users SET wechat_unionid=#{unionid}, updated_at=now() WHERE id=#{id} AND wechat_unionid IS NULL")
  void unionid(@Param("id") long id, @Param("unionid") String unionid);

  @Select("SELECT family_id FROM family_members WHERE user_id=#{id}")
  Long familyId(long id);

  @Select("SELECT row_to_json(f)::text FROM families f WHERE invite_code=#{code} FOR UPDATE")
  String invited(String code);

  @Select("SELECT count(*) FROM family_members WHERE family_id=#{id}")
  int memberCount(long id);

  @Select(
      "SELECT (to_jsonb(f)||jsonb_build_object('members',COALESCE((SELECT jsonb_agg(to_jsonb(m)||jsonb_build_object('user',to_jsonb(u)) ORDER BY m.joined_at,m.id) FROM family_members m JOIN yy_user_profiles u ON u.id=m.user_id WHERE m.family_id=f.id),'[]'::jsonb)))::text FROM families f WHERE f.id=#{id}")
  String family(long id);

  @Select(
      value =
          "INSERT INTO families(name,description,invite_code,owner_id) VALUES(#{name},#{description},#{code},#{user}) RETURNING id",
      affectData = true)
  long createFamily(
      @Param("name") String name,
      @Param("description") String description,
      @Param("code") String code,
      @Param("user") long user);

  @Insert("INSERT INTO family_members(family_id,user_id,role) VALUES(#{family},#{user},#{role})")
  void addMember(
      @Param("family") long family, @Param("user") long user, @Param("role") String role);
}

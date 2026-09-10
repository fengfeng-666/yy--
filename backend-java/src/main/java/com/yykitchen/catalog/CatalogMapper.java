package com.yykitchen.catalog;

import java.util.List;
import org.apache.ibatis.annotations.*;

@Mapper
public interface CatalogMapper {
  @Select(
      "SELECT row_to_json(d)::text FROM yy_dish_profiles d WHERE family_id=#{family} ORDER BY created_at DESC,id DESC")
  List<String> list(long family);

  @Select(
      "SELECT row_to_json(d)::text FROM yy_dish_profiles d WHERE family_id=#{family} AND id=#{id}")
  String detail(@Param("family") long family, @Param("id") long id);

  @Select(
      "SELECT COALESCE((SELECT version::text FROM yy_family_data_versions WHERE family_id=#{family}),'0')")
  String version(long family);

  @Select(
      value =
          "INSERT INTO dishes(family_id,name,description,price,image_url,is_available,need_prepare_ahead,suitable_for_weekday) VALUES(#{family},#{p.name},#{p.description},#{p.price},#{p.image_url},#{p.is_available},false,false) RETURNING id",
      affectData = true)
  long create(@Param("family") long family, @Param("p") CatalogController.DishRequest p);

  @Update(
      "UPDATE dishes SET name=#{p.name},description=#{p.description},price=#{p.price},image_url=#{p.image_url},is_available=#{p.is_available},updated_at=now() WHERE family_id=#{family} AND id=#{id}")
  int update(
      @Param("family") long family,
      @Param("id") long id,
      @Param("p") CatalogController.DishRequest p);

  @Select("SELECT count(*) FROM meal_order_items WHERE dish_id=#{id}")
  int orderReferences(long id);

  @Delete("DELETE FROM dishes WHERE family_id=#{family} AND id=#{id}")
  int delete(@Param("family") long family, @Param("id") long id);

  @Select(
      "SELECT row_to_json(p)::text FROM dish_preferences p JOIN dishes d ON d.id=p.dish_id WHERE d.family_id=#{family} ORDER BY p.id")
  List<String> preferences(long family);

  List<String> batch(@Param("family") long family, @Param("ids") List<Long> ids);
}

"use client";

import { useEffect, useState } from "react";
import { loadFavorites, toggleFavorite, syncFavoritesFromServer, pushFavoritesToServer } from "@/lib/favorites";
import { IconStar } from "@/components/icons";

export default function FavButton({ recipeId }: { recipeId: string }) {
  const [fav, setFav] = useState(false);
  useEffect(() => {
    (async () => {
      const ids = await syncFavoritesFromServer();
      setFav(ids.includes(recipeId));
    })();
  }, [recipeId]);

  const onToggle = () => {
    const ids = toggleFavorite(recipeId);
    setFav(ids.includes(recipeId));
    pushFavoritesToServer(ids);
  };

  return (
    <button
      className={fav ? "btn" : "btn ghost"}
      onClick={onToggle}
      style={{ padding: "10px 16px", fontSize: 14 }}
      aria-pressed={fav}
    >
      <IconStar size={16} filled={fav} />
      {fav ? "已收藏" : "收藏"}
    </button>
  );
}

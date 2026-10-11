import { useEffect, useState } from "react";
import { View } from "react-native";

import { applyThemePref, spacing, THEME_PREF_KEY, ThemePref } from "@/src/theme";
import { Segments, T } from "@/src/ui";
import { storage } from "@/src/utils/storage";

// Appearance picker: follow device / light / dark (persisted).
export function ThemeToggle() {
  const [pref, setPref] = useState<ThemePref>("system");
  useEffect(() => {
    storage.getItem<ThemePref>(THEME_PREF_KEY, "system").then((p) => setPref(p ?? "system"));
  }, []);
  const change = (p: ThemePref) => {
    setPref(p);
    applyThemePref(p);
    storage.setItem(THEME_PREF_KEY, p);
  };
  return (
    <View testID="theme-toggle" style={{ gap: spacing.xs }}>
      <T v="label">المظهر</T>
      <View style={{ marginHorizontal: -spacing.lg }}>
        <Segments value={pref} onChange={change} options={[{ key: "system", label: "تلقائي" }, { key: "light", label: "فاتح" }, { key: "dark", label: "داكن" }]} />
      </View>
    </View>
  );
}

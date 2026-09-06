import { useLayoutEffect } from "react";
import { useThree } from "@react-three/fiber";

/** demand frameloop için invalidate fonksiyonunu dışarı verir. */
export default function BindInvalidate({ invalidateRef }) {
  const invalidate = useThree((s) => s.invalidate);

  useLayoutEffect(() => {
    if (invalidateRef) invalidateRef.current = invalidate;
    invalidate();
    return () => {
      if (invalidateRef && invalidateRef.current === invalidate) {
        invalidateRef.current = null;
      }
    };
  }, [invalidate, invalidateRef]);

  return null;
}

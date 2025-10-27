import { useEffect, useRef, useState } from 'react';

type TState = {
    clientWidth: number | null,
    clientHeight: number | null,
    naturalWidth: number | null,
    naturalHeight: number | null,
    complete: boolean
}

export function useElementSize<T extends HTMLImageElement>() {
    const ref = useRef<T | null>(null)
    const [sizes, setSizes] = useState<TState>({
        clientWidth: null,
        clientHeight: null,
        naturalWidth: null,
        naturalHeight: null,
        complete: false,
    })

    useEffect(() => {
        if (!ref.current) {
            return;
        }
        const update = () => {
            if (!ref.current) {
                return;
            }
            setSizes({
                clientWidth: ref.current.clientWidth,
                clientHeight: ref.current.clientHeight,
                naturalWidth: ref.current.naturalWidth,
                naturalHeight: ref.current.naturalHeight,
                complete: ref.current.complete
            })
        }
        update()
        const ob = new ResizeObserver(update);
        ob.observe(ref.current)
        return () => {
            ob.disconnect()
        }
    }, [])

    return { ref, ...sizes }
}

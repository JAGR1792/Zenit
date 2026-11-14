---
name: frontend-patterns
description: Patrones de desarrollo frontend para React, Next.js, gestion de estado, optimizacion de rendimiento y buenas practicas de UI.
origin: ECC
---
# Patrones de Desarrollo Frontend

Pat
rones modernos de frontend para React, Next.j
s e interfaces de usuario de alto rendimiento
.

## Cuándo Activar

- Construir componente
s React (composición, props, renderizado)
- 
Gestionar estado (useState, useReducer, Zusta
nd, Context)
- Implementar obtención de dato
s (SWR, React Query, server components)
- Opt
imizar rendimiento (memoización, virtualizac
ión, code splitting)
- Trabajar con formular
ios (validación, inputs controlados, esquema
s Zod)
- Manejar routing y navegación del la
do del cliente
- Construir patrones de UI acc
esibles y responsivos

## Patrones de Compone
ntes

### Composición sobre Herencia

```typ
escript
// PASS: BIEN: Composición de compon
entes
interface CardProps {
  children: React
.ReactNode
  variant?: 'default' | 'outlined'

}

export function Card({ children, variant 
= 'default' }: CardProps) {
  return <div cla
ssName={`card card-${variant}`}>{children}</d
iv>
}

export function CardHeader({ children 
}: { children: React.ReactNode }) {
  return 
<div className="card-header">{children}</div>

}

export function CardBody({ children }: { 
children: React.ReactNode }) {
  return <div 
className="card-body">{children}</div>
}

// 
Uso
<Card>
  <CardHeader>Title</CardHeader>
 
 <CardBody>Content</CardBody>
</Card>
```

##
# Compound Components

```typescript
interfac
e TabsContextValue {
  activeTab: string
  se
tActiveTab: (tab: string) => void
}

const Ta
bsContext = createContext<TabsContextValue | 
undefined>(undefined)

export function Tabs({
 children, defaultTab }: {
  children: React.
ReactNode
  defaultTab: string
}) {
  const [
activeTab, setActiveTab] = useState(defaultTa
b)

  return (
    <TabsContext.Provider valu
e={{ activeTab, setActiveTab }}>
      {child
ren}
    </TabsContext.Provider>
  )
}

expor
t function TabList({ children }: { children: 
React.ReactNode }) {
  return <div className=
"tab-list">{children}</div>
}

export functio
n Tab({ id, children }: { id: string, childre
n: React.ReactNode }) {
  const context = use
Context(TabsContext)
  if (!context) throw ne
w Error('Tab must be used within Tabs')

  re
turn (
    <button
      className={context.a
ctiveTab === id ? 'active' : ''}
      onClic
k={() => context.setActiveTab(id)}
    >
    
  {children}
    </button>
  )
}

// Uso
<Tab
s defaultTab="overview">
  <TabList>
    <Tab
 id="overview">Overview</Tab>
    <Tab id="de
tails">Details</Tab>
  </TabList>
</Tabs>
```


### Patrón Render Props

```typescript
int
erface DataLoaderProps<T> {
  url: string
  c
hildren: (data: T | null, loading: boolean, e
rror: Error | null) => React.ReactNode
}

exp
ort function DataLoader<T>({ url, children }:
 DataLoaderProps<T>) {
  const [data, setData
] = useState<T | null>(null)
  const [loading
, setLoading] = useState(true)
  const [error
, setError] = useState<Error | null>(null)

 
 useEffect(() => {
    fetch(url)
      .then
(res => res.json())
      .then(setData)
    
  .catch(setError)
      .finally(() => setLo
ading(false))
  }, [url])

  return <>{childr
en(data, loading, error)}</>
}

// Uso
<DataL
oader<Market[]> url="/api/markets">
  {(marke
ts, loading, error) => {
    if (loading) ret
urn <Spinner />
    if (error) return <Error 
error={error} />
    return <MarketList marke
ts={markets!} />
  }}
</DataLoader>
```

## P
atrones de Custom Hooks

### Hook de Gestión
 de Estado

```typescript
export function use
Toggle(initialValue = false): [boolean, () =>
 void] {
  const [value, setValue] = useState
(initialValue)

  const toggle = useCallback(
() => {
    setValue(v => !v)
  }, [])

  ret
urn [value, toggle]
}

// Uso
const [isOpen, 
toggleOpen] = useToggle()
```

### Hook de Ob
tención de Datos Asíncrona

```typescript
i
nterface UseQueryOptions<T> {
  onSuccess?: (
data: T) => void
  onError?: (error: Error) =
> void
  enabled?: boolean
}

export function
 useQuery<T>(
  key: string,
  fetcher: () =>
 Promise<T>,
  options?: UseQueryOptions<T>
)
 {
  const [data, setData] = useState<T | nul
l>(null)
  const [error, setError] = useState
<Error | null>(null)
  const [loading, setLoa
ding] = useState(false)

  const refetch = us
eCallback(async () => {
    setLoading(true)

    setError(null)

    try {
      const res
ult = await fetcher()
      setData(result)
 
     options?.onSuccess?.(result)
    } catch
 (err) {
      const error = err as Error
   
   setError(error)
      options?.onError?.(e
rror)
    } finally {
      setLoading(false)

    }
  }, [fetcher, options])

  useEffect(
() => {
    if (options?.enabled !== false) {

      refetch()
    }
  }, [key, refetch, op
tions?.enabled])

  return { data, error, loa
ding, refetch }
}

// Uso
const { data: marke
ts, loading, error, refetch } = useQuery(
  '
markets',
  () => fetch('/api/markets').then(
r => r.json()),
  {
    onSuccess: data => co
nsole.log('Fetched', data.length, 'markets'),

    onError: err => console.error('Failed:',
 err)
  }
)
```

### Hook de Debounce

```typ
escript
export function useDebounce<T>(value:
 T, delay: number): T {
  const [debouncedVal
ue, setDebouncedValue] = useState<T>(value)


  useEffect(() => {
    const handler = setTi
meout(() => {
      setDebouncedValue(value)

    }, delay)

    return () => clearTimeout(
handler)
  }, [value, delay])

  return debou
ncedValue
}

// Uso
const [searchQuery, setSe
archQuery] = useState('')
const debouncedQuer
y = useDebounce(searchQuery, 500)

useEffect(
() => {
  if (debouncedQuery) {
    performSe
arch(debouncedQuery)
  }
}, [debouncedQuery])

```

## Patrones de Gestión de Estado

### 
Patrón Context + Reducer

```typescript
inte
rface State {
  markets: Market[]
  selectedM
arket: Market | null
  loading: boolean
}

ty
pe Action =
  | { type: 'SET_MARKETS'; payloa
d: Market[] }
  | { type: 'SELECT_MARKET'; pa
yload: Market }
  | { type: 'SET_LOADING'; pa
yload: boolean }

function reducer(state: Sta
te, action: Action): State {
  switch (action
.type) {
    case 'SET_MARKETS':
      return
 { ...state, markets: action.payload }
    ca
se 'SELECT_MARKET':
      return { ...state, 
selectedMarket: action.payload }
    case 'SE
T_LOADING':
      return { ...state, loading:
 action.payload }
    default:
      return s
tate
  }
}

const MarketContext = createConte
xt<{
  state: State
  dispatch: Dispatch<Acti
on>
} | undefined>(undefined)

export functio
n MarketProvider({ children }: { children: Re
act.ReactNode }) {
  const [state, dispatch] 
= useReducer(reducer, {
    markets: [],
    
selectedMarket: null,
    loading: false
  })


  return (
    <MarketContext.Provider valu
e={{ state, dispatch }}>
      {children}
   
 </MarketContext.Provider>
  )
}

export func
tion useMarkets() {
  const context = useCont
ext(MarketContext)
  if (!context) throw new 
Error('useMarkets must be used within MarketP
rovider')
  return context
}
```

## Optimiza
ción de Rendimiento

### Memoización

```ty
pescript
// PASS: useMemo para cómputos cost
osos
const sortedMarkets = useMemo(() => {
  
return markets.sort((a, b) => b.volume - a.vo
lume)
}, [markets])

// PASS: useCallback par
a funciones pasadas a hijos
const handleSearc
h = useCallback((query: string) => {
  setSea
rchQuery(query)
}, [])

// PASS: React.memo p
ara componentes puros
export const MarketCard
 = React.memo<MarketCardProps>(({ market }) =
> {
  return (
    <div className="market-car
d">
      <h3>{market.name}</h3>
      <p>{ma
rket.description}</p>
    </div>
  )
})
```


### Code Splitting y Carga Diferida

```types
cript
import { lazy, Suspense } from 'react'


// PASS: Carga diferida de componentes pesad
os
const HeavyChart = lazy(() => import('./He
avyChart'))
const ThreeJsBackground = lazy(()
 => import('./ThreeJsBackground'))

export fu
nction Dashboard() {
  return (
    <div>
   
   <Suspense fallback={<ChartSkeleton />}>
  
      <HeavyChart data={data} />
      </Susp
ense>

      <Suspense fallback={null}>
     
   <ThreeJsBackground />
      </Suspense>
  
  </div>
  )
}
```

### Virtualización para 
Listas Largas

```typescript
import { useVirt
ualizer } from '@tanstack/react-virtual'

exp
ort function VirtualMarketList({ markets }: {
 markets: Market[] }) {
  const parentRef = u
seRef<HTMLDivElement>(null)

  const virtuali
zer = useVirtualizer({
    count: markets.len
gth,
    getScrollElement: () => parentRef.cu
rrent,
    estimateSize: () => 100,  // Altur
a estimada de fila
    overscan: 5  // Elemen
tos extra a renderizar
  })

  return (
    <
div ref={parentRef} style={{ height: '600px',
 overflow: 'auto' }}>
      <div
        styl
e={{
          height: `${virtualizer.getTota
lSize()}px`,
          position: 'relative'
 
       }}
      >
        {virtualizer.getVir
tualItems().map(virtualRow => (
          <di
v
            key={virtualRow.index}
        
    style={{
              position: 'absolut
e',
              top: 0,
              left:
 0,
              width: '100%',
            
  height: `${virtualRow.size}px`,
           
   transform: `translateY(${virtualRow.start}
px)`
            }}
          >
            <
MarketCard market={markets[virtualRow.index]}
 />
          </div>
        ))}
      </div>

    </div>
  )
}
```

## Patrones de Manejo 
de Formularios

### Formulario Controlado con
 Validación

```typescript
interface FormDat
a {
  name: string
  description: string
  en
dDate: string
}

interface FormErrors {
  nam
e?: string
  description?: string
  endDate?:
 string
}

export function CreateMarketForm()
 {
  const [formData, setFormData] = useState
<FormData>({
    name: '',
    description: '
',
    endDate: ''
  })

  const [errors, set
Errors] = useState<FormErrors>({})

  const v
alidate = (): boolean => {
    const newError
s: FormErrors = {}

    if (!formData.name.tr
im()) {
      newErrors.name = 'Name is requi
red'
    } else if (formData.name.length > 20
0) {
      newErrors.name = 'Name must be und
er 200 characters'
    }

    if (!formData.d
escription.trim()) {
      newErrors.descript
ion = 'Description is required'
    }

    if
 (!formData.endDate) {
      newErrors.endDat
e = 'End date is required'
    }

    setErro
rs(newErrors)
    return Object.keys(newError
s).length === 0
  }

  const handleSubmit = a
sync (e: React.FormEvent) => {
    e.preventD
efault()

    if (!validate()) return

    tr
y {
      await createMarket(formData)
      
// Manejo de éxito
    } catch (error) {
   
   // Manejo de error
    }
  }

  return (
 
   <form onSubmit={handleSubmit}>
      <inpu
t
        value={formData.name}
        onCha
nge={e => setFormData(prev => ({ ...prev, nam
e: e.target.value }))}
        placeholder="M
arket name"
      />
      {errors.name && <s
pan className="error">{errors.name}</span>}


      {/* Otros campos */}

      <button typ
e="submit">Create Market</button>
    </form>

  )
}
```

## Patrón Error Boundary

```typ
escript
interface ErrorBoundaryState {
  hasE
rror: boolean
  error: Error | null
}

export
 class ErrorBoundary extends React.Component<

  { children: React.ReactNode },
  ErrorBoun
daryState
> {
  state: ErrorBoundaryState = {

    hasError: false,
    error: null
  }

  
static getDerivedStateFromError(error: Error)
: ErrorBoundaryState {
    return { hasError:
 true, error }
  }

  componentDidCatch(error
: Error, errorInfo: React.ErrorInfo) {
    co
nsole.error('Error boundary caught:', error, 
errorInfo)
  }

  render() {
    if (this.sta
te.hasError) {
      return (
        <div cl
assName="error-fallback">
          <h2>Somet
hing went wrong</h2>
          <p>{this.state
.error?.message}</p>
          <button onClic
k={() => this.setState({ hasError: false })}>

            Try again
          </button>
  
      </div>
      )
    }

    return this.p
rops.children
  }
}

// Uso
<ErrorBoundary>
 
 <App />
</ErrorBoundary>
```

## Patrones de
 Animación

### Animaciones con Framer Motio
n

```typescript
import { motion, AnimatePres
ence } from 'framer-motion'

// PASS: Animaci
ones de lista
export function AnimatedMarketL
ist({ markets }: { markets: Market[] }) {
  r
eturn (
    <AnimatePresence>
      {markets.
map(market => (
        <motion.div
         
 key={market.id}
          initial={{ opacity
: 0, y: 20 }}
          animate={{ opacity: 1
, y: 0 }}
          exit={{ opacity: 0, y: -2
0 }}
          transition={{ duration: 0.3 }}

        >
          <MarketCard market={mark
et} />
        </motion.div>
      ))}
    </
AnimatePresence>
  )
}

// PASS: Animaciones 
de modal
export function Modal({ isOpen, onCl
ose, children }: ModalProps) {
  return (
   
 <AnimatePresence>
      {isOpen && (
       
 <>
          <motion.div
            classNa
me="modal-overlay"
            initial={{ opa
city: 0 }}
            animate={{ opacity: 1 
}}
            exit={{ opacity: 0 }}
        
    onClick={onClose}
          />
          
<motion.div
            className="modal-cont
ent"
            initial={{ opacity: 0, scale
: 0.9, y: 20 }}
            animate={{ opacit
y: 1, scale: 1, y: 0 }}
            exit={{ o
pacity: 0, scale: 0.9, y: 20 }}
          >
 
           {children}
          </motion.div>

        </>
      )}
    </AnimatePresence>

  )
}
```

## Patrones de Accesibilidad

### 
Navegación por Teclado

```typescript
export
 function Dropdown({ options, onSelect }: Dro
pdownProps) {
  const [isOpen, setIsOpen] = u
seState(false)
  const [activeIndex, setActiv
eIndex] = useState(0)

  const handleKeyDown 
= (e: React.KeyboardEvent) => {
    switch (e
.key) {
      case 'ArrowDown':
        e.pre
ventDefault()
        setActiveIndex(i => Mat
h.min(i + 1, options.length - 1))
        bre
ak
      case 'ArrowUp':
        e.preventDef
ault()
        setActiveIndex(i => Math.max(i
 - 1, 0))
        break
      case 'Enter':
 
       e.preventDefault()
        onSelect(op
tions[activeIndex])
        setIsOpen(false)

        break
      case 'Escape':
        se
tIsOpen(false)
        break
    }
  }

  ret
urn (
    <div
      role="combobox"
      ar
ia-expanded={isOpen}
      aria-haspopup="lis
tbox"
      onKeyDown={handleKeyDown}
    >
 
     {/* Implementación del Dropdown */}
   
 </div>
  )
}
```

### Gestión de Foco

```t
ypescript
export function Modal({ isOpen, onC
lose, children }: ModalProps) {
  const modal
Ref = useRef<HTMLDivElement>(null)
  const pr
eviousFocusRef = useRef<HTMLElement | null>(n
ull)

  useEffect(() => {
    if (isOpen) {
 
     // Guardar elemento actualmente enfocado

      previousFocusRef.current = document.ac
tiveElement as HTMLElement

      // Enfocar 
modal
      modalRef.current?.focus()
    } e
lse {
      // Restaurar foco al cerrar
     
 previousFocusRef.current?.focus()
    }
  },
 [isOpen])

  return isOpen ? (
    <div
    
  ref={modalRef}
      role="dialog"
      ar
ia-modal="true"
      tabIndex={-1}
      onK
eyDown={e => e.key === 'Escape' && onClose()}

    >
      {children}
    </div>
  ) : null

}
```

**Recuerda**: Los patrones modernos d
e frontend permiten interfaces de usuario man
tenibles y de alto rendimiento. Elige los pat
rones que se ajusten a la complejidad de tu p
royecto.



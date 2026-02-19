import { useState, useEffect } from "react";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";
import { Plus, Trash2, FileText, Loader2 } from "lucide-react";

interface PuntoVenta {
    id: number;
    numero: number;
    cuit: string;
    es_produccion: boolean;
}

interface ItemFactura {
    descripcion: string;
    cantidad: number;
    precio_unitario: number;
    alicuota_iva: number;
    subtotal: number;
}

export function Facturador() {
    const { toast } = useToast();
    const [puntos, setPuntos] = useState<PuntoVenta[]>([]);
    const [selectedPunto, setSelectedPunto] = useState<string>("");

    // Datos Cliente
    const [clienteNombre, setClienteNombre] = useState("");
    const [clienteDoc, setClienteDoc] = useState("");
    const [clienteDireccion, setClienteDireccion] = useState("");
    const [clienteCondicion, setClienteCondicion] = useState("Consumidor Final");

    // Items
    const [items, setItems] = useState<ItemFactura[]>([
        { descripcion: "", cantidad: 1, precio_unitario: 0, alicuota_iva: 21, subtotal: 0 }
    ]);

    const [loading, setLoading] = useState(false);
    const [ultimoComprobante, setUltimoComprobante] = useState<any>(null);

    useEffect(() => {
        fetchPuntos();
    }, []);

    const fetchPuntos = async () => {
        try {
            const response = await api.get("/puntos-venta/");
            setPuntos(response.data);
            if (response.data.length > 0) {
                setSelectedPunto(response.data[0].id.toString());
            }
        } catch (error) {
            console.error("Error cargando puntos de venta:", error);
        }
    };

    // Auto-completar documento para CF si está vacío
    const handleCondicionChange = (val: string) => {
        setClienteCondicion(val);
        if (val === "Consumidor Final" && !clienteDoc) {
            setClienteDoc("00000000");
        }
    };

    const updateItem = (index: number, field: keyof ItemFactura, value: any) => {
        const newItems = [...items];
        newItems[index] = { ...newItems[index], [field]: value };

        // Recalcular subtotal
        if (field === "cantidad" || field === "precio_unitario") {
            const qty = field === "cantidad" ? parseFloat(value) || 0 : newItems[index].cantidad;
            const price = field === "precio_unitario" ? parseFloat(value) || 0 : newItems[index].precio_unitario;
            newItems[index].subtotal = qty * price;
        }

        setItems(newItems);
    };

    const addItem = () => {
        setItems([...items, { descripcion: "", cantidad: 1, precio_unitario: 0, alicuota_iva: 21, subtotal: 0 }]);
    };

    const removeItem = (index: number) => {
        if (items.length === 1) return;
        setItems(items.filter((_, i) => i !== index));
    };

    const calculateTotals = () => {
        const totalNeto = items.reduce((acc, item) => acc + (item.subtotal / 1.21), 0); // Simplificado
        const totalIva = items.reduce((acc, item) => acc + (item.subtotal - (item.subtotal / 1.21)), 0);
        const total = items.reduce((acc, item) => acc + item.subtotal, 0);
        return { totalNeto, totalIva, total };
    };

    const handleGenerarFactura = async () => {
        if (!selectedPunto || !clienteNombre || !clienteDoc) {
            toast({
                title: "Faltan datos",
                description: "Por favor complete Punto de Venta, Nombre, CUIT/DNI y Condición del cliente.",
                variant: "destructive",
            });
            return;
        }

        const totals = calculateTotals();
        setLoading(true);

        try {
            // Determinar tipo documento AFIP
            // 99 = Consumidor Final, 80 = CUIT, 96 = DNI
            let tipoDoc = 80;
            if (clienteCondicion === "Consumidor Final") {
                // Si es CF y tiene DNI/00000000 usamos 99 o 96
                // Simplificación: si es < 11 digitos es DNI (96), si es 00000000 es CF (99)
                // O mas simple: Default 99 si es CF, 80 para los demas (que requieren CUIT)
                tipoDoc = 99; // Default genérico que suele funcionar para CF
                if (clienteDoc.length < 11 && clienteDoc !== "00000000") tipoDoc = 96; // DNI
            }

            const payload = {
                punto_venta_id: parseInt(selectedPunto),
                cliente_detalle: {
                    nombre: clienteNombre,
                    numero_documento: clienteDoc,
                    condicion_iva: clienteCondicion,
                    direccion: clienteDireccion,
                    tipo_documento: tipoDoc
                },
                tipo_comprobante: 11, // Factura C por defecto
                items: items.map(i => ({
                    descripcion: i.descripcion,
                    cantidad: i.cantidad,
                    precio_unitario: i.precio_unitario,
                    alicuota_iva: 21.0,
                    subtotal: i.subtotal,
                    producto_id: null
                })),
                total_neto: totals.totalNeto,
                total_iva: totals.totalIva,
                total_comprobante: totals.total
            };


            const response = await api.post("/facturas/", payload);

            setUltimoComprobante(response.data);
            toast({
                title: "Factura Generada",
                description: `CAE: ${response.data.cae} - Número: ${response.data.numero}`,
                className: "bg-green-500 text-white",
            });

        } catch (error: any) {
            console.error("Error generando factura:", error);
            toast({
                title: "Error",
                description: error.response?.data?.detail || "Error interno del servidor",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <FileText className="h-6 w-6" />
                        Nueva Factura
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* Cabecera */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Punto de Venta</Label>
                            <Select value={selectedPunto} onValueChange={setSelectedPunto}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Seleccionar PV" />
                                </SelectTrigger>
                                <SelectContent>
                                    {puntos.map(pv => (
                                        <SelectItem key={pv.id} value={pv.id.toString()}>
                                            {pv.numero} - {pv.es_produccion ? "Prod" : "Test"} ({pv.cuit})
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>Tipo Comprobante</Label>
                            <Input value="Factura C (11)" disabled />
                        </div>
                    </div>

                    {/* Cliente */}
                    <div className="border rounded-md p-4 space-y-4">
                        <h3 className="font-semibold text-sm text-muted-foreground">Datos del Cliente</h3>
                        <div className="space-y-2">
                            <Label>Condición frente al IVA</Label>
                            <Select value={clienteCondicion} onValueChange={handleCondicionChange}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Seleccionar Condición" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Consumidor Final">Consumidor Final</SelectItem>
                                    <SelectItem value="Responsable Inscripto">Responsable Inscripto</SelectItem>
                                    <SelectItem value="Monotributo">Monotributo</SelectItem>
                                    <SelectItem value="Exento">Exento</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>Nombre / Razón Social</Label>
                            <Input value={clienteNombre} onChange={e => setClienteNombre(e.target.value)} placeholder="Nombre Cliente" />
                        </div>
                        <div className="space-y-2">
                            <Label>CUIT / DNI</Label>
                            <Input value={clienteDoc} onChange={e => setClienteDoc(e.target.value)} placeholder="Sin guiones" />
                        </div>
                        <div className="space-y-2">
                            <Label>Dirección</Label>
                            <Input value={clienteDireccion} onChange={e => setClienteDireccion(e.target.value)} placeholder="Calle 123" />
                        </div>
                    </div>

                    {/* Items */}
                    <div className="border rounded-md overflow-hidden">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="w-[40%]">Descripción</TableHead>
                                    <TableHead className="w-[15%]">Cant.</TableHead>
                                    <TableHead className="w-[20%]">Precio Unit.</TableHead>
                                    <TableHead className="w-[20%]">Subtotal</TableHead>
                                    <TableHead className="w-[5%]"></TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {items.map((item, idx) => (
                                    <TableRow key={idx}>
                                        <TableCell>
                                            <Input
                                                value={item.descripcion}
                                                onChange={e => updateItem(idx, "descripcion", e.target.value)}
                                                placeholder="Producto o Servicio"
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <Input
                                                type="number"
                                                value={item.cantidad}
                                                onChange={e => updateItem(idx, "cantidad", e.target.value)}
                                                min="1"
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <Input
                                                type="number"
                                                value={item.precio_unitario}
                                                onChange={e => updateItem(idx, "precio_unitario", e.target.value)}
                                                min="0"
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <div className="font-medium px-3">
                                                ${item.subtotal.toFixed(2)}
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <Button variant="ghost" size="icon" onClick={() => removeItem(idx)} className="text-destructive">
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                        <div className="p-2 bg-muted/20">
                            <Button variant="outline" size="sm" onClick={addItem} className="w-full border-dashed">
                                <Plus className="h-4 w-4 mr-2" /> Agregar Ítem
                            </Button>
                        </div>
                    </div>

                    {/* Totales y Acción */}
                    <div className="flex justify-end items-center gap-8 pt-4">
                        <div className="text-right space-y-1">
                            <div className="text-sm text-muted-foreground">Neto: ${calculateTotals().totalNeto.toFixed(2)}</div>
                            <div className="text-sm text-muted-foreground">IVA (21%): ${calculateTotals().totalIva.toFixed(2)}</div>
                            <div className="text-2xl font-bold">Total: ${calculateTotals().total.toFixed(2)}</div>
                        </div>
                        <Button size="lg" onClick={handleGenerarFactura} disabled={loading}>
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {loading ? "Generando..." : "Generar Factura"}
                        </Button>
                    </div>

                    {/* Resultado */}
                    {ultimoComprobante && (
                        <div className={`mt-6 p-4 border rounded-md animate-in zoom-in-50 duration-300 ${ultimoComprobante.resultado_afip === "A" || ultimoComprobante.resultado_afip === "Aprobado" ? "bg-green-50 border-green-200 text-green-800" : "bg-red-50 border-red-200 text-red-800"}`}>
                            <h4 className="font-bold flex items-center gap-2">
                                {ultimoComprobante.resultado_afip === "A" || ultimoComprobante.resultado_afip === "Aprobado" ? "✅ Comprobante Autorizado" : "❌ Comprobante Rechazado"}
                            </h4>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2">
                                <div>
                                    <span className={`text-xs block ${ultimoComprobante.resultado_afip === "A" || ultimoComprobante.resultado_afip === "Aprobado" ? "text-green-600" : "text-red-600"}`}>CAE</span>
                                    <span className="font-mono text-lg">{ultimoComprobante.cae || "-"}</span>
                                </div>
                                <div>
                                    <span className={`text-xs block ${ultimoComprobante.resultado_afip === "A" || ultimoComprobante.resultado_afip === "Aprobado" ? "text-green-600" : "text-red-600"}`}>Vencimiento CAE</span>
                                    <span className="font-mono">{ultimoComprobante.vto_cae || "-"}</span>
                                </div>
                                <div>
                                    <span className={`text-xs block ${ultimoComprobante.resultado_afip === "A" || ultimoComprobante.resultado_afip === "Aprobado" ? "text-green-600" : "text-red-600"}`}>Número</span>
                                    <span className="font-mono">{ultimoComprobante.numero}</span>
                                </div>
                                <div>
                                    <span className={`text-xs block ${ultimoComprobante.resultado_afip === "A" || ultimoComprobante.resultado_afip === "Aprobado" ? "text-green-600" : "text-red-600"}`}>Resultado</span>
                                    <span className="font-bold">{ultimoComprobante.resultado_afip}</span>
                                </div>
                            </div>
                            {ultimoComprobante.observaciones_afip && (
                                <div className="mt-4 pt-4 border-t border-black/10">
                                    <span className="text-xs font-bold block mb-1">Observaciones AFIP:</span>
                                    <p className="text-sm font-mono whitespace-pre-wrap">
                                        {ultimoComprobante.observaciones_afip}
                                    </p>
                                </div>
                            )}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div >
    );
}

import { useState } from "react";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";

interface PuntoVentaFormProps {
    onSuccess: () => void;
}

export function PuntoVentaForm({ onSuccess }: PuntoVentaFormProps) {
    const { toast } = useToast();
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        numero: "",
        nombre: "",
        cuit: "",
        es_produccion: false,
    });
    const [certificado, setCertificado] = useState<File | null>(null);
    const [clavePrivada, setClavePrivada] = useState<File | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!certificado || !clavePrivada) {
            toast({
                title: "Error",
                description: "Debes subir el certificado (.crt) y la clave privada (.key)",
                variant: "destructive",
            });
            return;
        }

        setLoading(true);
        const data = new FormData();
        data.append("numero", formData.numero);
        data.append("nombre", formData.nombre);
        data.append("cuit", formData.cuit);
        data.append("es_produccion", String(formData.es_produccion));
        data.append("certificado", certificado);
        data.append("clave_privada", clavePrivada);

        try {
            await api.post("/puntos-venta/", data, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            toast({
                title: "Punto de Venta creado",
                description: "La configuración se ha guardado correctamente.",
            });
            onSuccess();
            setFormData({ numero: "", nombre: "", cuit: "", es_produccion: false });
            setCertificado(null);
            setClavePrivada(null);
        } catch (error) {
            console.error(error);
            toast({
                title: "Error",
                description: "No se pudo guardar el punto de venta.",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card className="w-full max-w-md mx-auto">
            <CardHeader>
                <CardTitle>Nuevo Punto de Venta</CardTitle>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid w-full items-center gap-1.5">
                        <Label htmlFor="numero">Número de Punto de Venta (AFIP)</Label>
                        <Input
                            id="numero"
                            type="number"
                            value={formData.numero}
                            onChange={(e) => setFormData({ ...formData, numero: e.target.value })}
                            required
                        />
                    </div>

                    <div className="grid w-full items-center gap-1.5">
                        <Label htmlFor="cuit">CUIT Emisor</Label>
                        <Input
                            id="cuit"
                            type="text"
                            value={formData.cuit}
                            onChange={(e) => setFormData({ ...formData, cuit: e.target.value })}
                            required
                        />
                    </div>

                    <div className="flex items-center space-x-2">
                        <Switch
                            id="production-mode"
                            checked={formData.es_produccion}
                            onCheckedChange={(checked) => setFormData({ ...formData, es_produccion: checked })}
                        />
                        <Label htmlFor="production-mode">
                            {formData.es_produccion ? "Modo PRODUCCIÓN (Real)" : "Modo TESTING (Homologación)"}
                        </Label>
                    </div>

                    <div className="grid w-full items-center gap-1.5">
                        <Label htmlFor="certificado">Certificado (.crt)</Label>
                        <Input
                            id="certificado"
                            type="file"
                            accept=".crt"
                            onChange={(e) => setCertificado(e.target.files?.[0] || null)}
                            required
                        />
                    </div>

                    <div className="grid w-full items-center gap-1.5">
                        <Label htmlFor="key">Clave Privada (.key)</Label>
                        <Input
                            id="key"
                            type="file"
                            accept=".key"
                            onChange={(e) => setClavePrivada(e.target.files?.[0] || null)}
                            required
                        />
                    </div>

                    <Button type="submit" className="w-full" disabled={loading}>
                        {loading ? "Guardando..." : "Guardar Configuración"}
                    </Button>
                </form>
            </CardContent>
        </Card>
    );
}

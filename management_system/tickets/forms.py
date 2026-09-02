from django import forms #libreria para validar los formularios
from .models import Ticket #importacion del objeto Ticket


## FORM SE ENCARGARA DE VALIDAR LOS DATOS DE LOS FORMULARIOS CON LA LIBRERIA DE DJANGO "FORMS" ###


class TicketForm(forms.ModelForm):
    class Meta:

        model = Ticket

#LISTA CON LOS CAMPOS QUE VALIDARA, SI SE INTENTA MANIPULAR EL HTML PARA MANDAR OTROS CAMPOS NO SERAN ACEPTADO
        fields = [
            "titulo",
            "descripcion",
            "prioridad",
            "departamento_destino"
        ]
# LISTA DE LABELS PARA LOS CAMPOS(FIELD) A LOS QUE ESTARAN ASOCIADOS

        labels = {
            "titulo": "Título",
            "descripcion" : "Descripción",
            "prioridad" : "Prioridad",
            "departamento_destino" : "Departamento Asignado"
        }

#Help Text, APOYO DESCRIPTIVO PARA EL USUARIO

        help_texts = {
            "titulo": "Escribe un resumen del problema.",
            "descripcion": "Por favor, explica qué ocurrió y qué necesitas.",
            "prioridad": "Selecciona la importancia de la solicitud.",
            "departamento_destino": "Selecciona el departamento que debe atenderla.",
        }

#WIDGETS, ESTOS SE PINTARAN EN PANTALLA, DESDE AQUI SE LE DEFINEN LOS ATRIBUTOS VISUALES QUE TENDRA CADA CAMPO
        widgets = {
            "titulo" : forms.TextInput(
                attrs= {
                    "class" : "form-control",
                    "placeholder" : "Ejemplo: No funciona la impresora"
                }
            ),
            "descripcion" : forms.Textarea(
                attrs= {
                    "class" : "form-control",
                    "placeholder" : "Describe el problema con el mayor detalle posible",
                    "rows" : 4
                }
            ),
            "prioridad" : forms.Select(
                attrs= {
                    "class" : "form-select"
                }
            ),
            "departamento_destino": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[
            "departamento_destino"
        ].empty_label = "Selecciona un departamento"
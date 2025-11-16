from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto, Categoria, Inventario, Venta, Detalle_venta
from .forms import ProductoForm, CategoriaForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from decimal import Decimal

# Create your views here.


def home(request):
    return render(request, 'tienda/inicio/home.html')
# <---------------vistas de producto------------>
@login_required
def ProductoListView(request):
    return render(request, 'tienda/producto/producto_list.html', {'productos':Producto.objects.all()})

def InventarioListView(request):
    return render(request, 'tienda/inventario/inventario_list.html', {'productos':Producto.objects.all()})

def ProductoCreateView(request):
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES or None)
        if form.is_valid():
            producto = form.save()
            stock = request.POST.get('stock')
            Inventario.objects.create(producto=producto, stock=stock)
            return redirect('producto-list')
    else:
        form = ProductoForm()
    return render(request, 'tienda/producto/producto_form.html', {'form': form, 'action': 'Crear'})

@login_required
def ProductoDeleteView(request, id):
    producto=get_object_or_404(Producto, pk=id)
    if request.method=="POST":
        producto.delete()
        return redirect('producto-list')
    return render(request, 'tienda/producto/producto_delete.html')

@login_required
def ProductoUpdateView(request, id):
    producto = get_object_or_404(Producto, pk=id) 
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES or None, instance=producto)
        if form.is_valid():
            producto = form.save()
            stock = request.POST.get('stock')
            Inventario.objects.update_or_create(producto=producto, defaults={'stock': stock})
            return redirect('producto-list')
    else:
        form = ProductoForm(instance=producto, initial={'stock': producto.inventario.stock})
    return render(request, 'tienda/producto/producto_form.html', {'form': form, 'action': 'Modificar'})
# <---------------vistas de categoria------------>
@login_required
def CategoriaListView(request):
    return render(request, 'tienda/categoria/categoria_list.html', {'categorias':Categoria.objects.all()})

@login_required
def CategoriaCreateView(request):
    if request.method=="POST":
        form=CategoriaForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            form.save()
            return redirect('categoria-list')
    else:
        form=CategoriaForm()
    return render(request, 'tienda/categoria/categoria_form.html', {'form':form, 'action':'Crear'})

@login_required
def CategoriaDeleteView(request, id):
    categoria=get_object_or_404(Categoria, pk=id)
    if request.method=="POST":
        categoria.delete()
        return redirect('categoria-list')
    return render(request, 'tienda/categoria/categoria_delete.html')

@login_required
def buscar_inventario(request):
    query = request.GET.get('buscar', '').strip()
    productos = Producto.objects.filter(nombre__icontains=query) if query else Producto.objects.all()
    return render(request, 'tienda/inventario/inventario_list.html', {
        'productos': productos,
        'query': query
    })

def buscar_producto(request):
    query = request.GET.get('buscar', '')
    categoria_id = request.GET.get('categoria', '')
    
    productos = Producto.objects.all()
    
    
    if query:
        productos = productos.filter(nombre__icontains=query)
    
    if categoria_id:
        productos = productos.filter(categoria__id=categoria_id)
    
    categorias = Categoria.objects.all()
    
    return render(request, 'tienda/producto/producto_list.html', {
        'productos': productos,
        'categorias': categorias,
        'query': query,
        'categoria_seleccionada': categoria_id
    })

@login_required
def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    venta, _ = Venta.objects.get_or_create(usuario=request.user, estado='pendiente', defaults={'estado': 'pendiente'})
    item, creado = Detalle_venta.objects.get_or_create(
        venta=venta,
        producto=producto,
        defaults={'precio_unitario': producto.precio, 'cantidad': 1}
    )
    if not creado:
        item.cantidad += 1
        item.precio_unitario = producto.precio 
        item.save()

    return redirect('producto-list')

def ver_carrito(request):
    venta, _ = Venta.objects.get_or_create(usuario=request.user, estado='pendiente', defaults={'estado': 'pendiente'})
    
    items = venta.detalle_venta_set.all()
    total = venta.total()

    return render(request, 'tienda/carrito/ver_carrito.html', {
        'venta': venta,
        'items': items,
        'total': total,
    })

@login_required
def incrementar_item(request, item_id):
    item = get_object_or_404(Detalle_venta, id=item_id)
    item.cantidad += 1
    item.save()
    return redirect('ver_carrito')


@login_required
def disminuir_item(request, item_id):
    item = get_object_or_404(Detalle_venta, id=item_id)
    if item.cantidad > 1:
        item.cantidad -= 1
        item.save()
    else:
        item.delete()
    return redirect('ver_carrito')


@login_required
def eliminar_item(request, item_id):
    item = get_object_or_404(Detalle_venta, id=item_id)
    item.delete()
    return redirect('ver_carrito')


@login_required
def vaciar_carrito(request):
    venta, _ = Venta.objects.get_or_create(usuario=request.user, estado='pendiente', defaults={'estado': 'pendiente'})
    venta.detalle_venta_set.all().delete()
    return redirect('ver_carrito')


@login_required
def resumen_pago(request):
    venta, _ = Venta.objects.get_or_create(usuario=request.user, estado='pendiente', defaults={'estado': 'pendiente'})
    items = venta.detalle_venta_set.all()

    if not items.exists():
        return redirect('ver_carrito')

    subtotal = venta.total() 
    
    iva = Decimal('0.19') * Decimal(subtotal)
    total_con_iva = subtotal + iva
   

    contexto = {
        'venta': venta,
        'items': items,
        'subtotal': subtotal,
        'iva': iva,
        'total_con_iva': total_con_iva,
    }
    
    return render(request, 'tienda/carrito/resumen.html', contexto)

@login_required
def pagar(request):
    venta = get_object_or_404(Venta, usuario=request.user, estado='pendiente')
    items = venta.detalle_venta_set.all()

    for item in items:
        try:
            inventario = Inventario.objects.get(producto=item.producto)
            inventario.stock -= item.cantidad
            inventario.save()
        except Inventario.DoesNotExist:
           pass
    
    
    venta.estado = 'pagada'
    venta.save()
    
    return render(request, 'tienda/carrito/pago.html')


@login_required
def reporte_ventas(request):
    ventas_pagadas = Venta.objects.filter(estado='pagada')
    return render(request, 'tienda/reporte/reporte_ventas.html', {'ventas': ventas_pagadas})

document.addEventListener("DOMContentLoaded",function(){let cartId=localStorage.getItem("cartId");if(!cartId){createCart();}else{fetchCartItems(cartId);}
document.querySelector("#apply-discount-btn").addEventListener("click",function(event){event.preventDefault();let discountCode=document.querySelector("#discount-code-input").value;applyDiscount(cartId,discountCode);});});function applyDiscount(cartId,discountCode){fetch(`/shop/cart/${cartId}/apply_discount/`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({discount_code:discountCode})}).then(response=>{if(response.ok){alert('Discount applied!')
fetchCartItems(cartId);}else{alert(`Failed to apply discount: ${response.statusText}`,)
console.error("Failed to apply discount:",response.statusText);}}).catch(error=>console.error("Error applying discount:",error));}
function createCart(){fetch("/shop/cart/",{method:"POST"}).then(response=>response.json()).then(data=>{localStorage.setItem("cartId",data.id);fetchCartItems(data.id);}).catch(error=>console.error("Error creating cart:",error));}
function fetchCartItems(cartId){fetch(`/shop/cart/${cartId}/`).then(response=>response.json()).then(data=>{populateCartTable(data);}).catch(error=>console.error("Error fetching cart items:",error));}
function populateCartTable(cartItem){const tableBody=document.querySelector("tbody");tableBody.innerHTML="";let cartItems=cartItem.items
cartItems.forEach(item=>{const row=document.createElement("tr");row.innerHTML=`
                <td>
                    <div class="media">

                        <div class="media-body">
                            <p>${item.product.title}</p>
                        </div>
                    </div>
                </td>
                <td><h5>${item.product.price}</h5></td>
                <td dir="ltr">
                    <div class="product_count">
                        <input id="quantity-${item.id}" type="text" name="qty" maxlength="12" value="${item.quantity}" title="Quantity:" class="input-text qty">
                        <button class="increase items-count" type="button"><i class="lnr lnr-chevron-up"></i></button>
                        <button class="reduced items-count" type="button"><i class="lnr lnr-chevron-down"></i></button>
                    </div>
                </td>
                <td><h5>${item.total_price}</h5></td>
                <td><button class="genric-btn danger circle delete-button">حذف</button></td>
            `;row.querySelector(".increase").addEventListener("click",()=>{updateQuantity(item.id,parseInt(document.getElementById(`quantity-${item.id}`).value)+1);});row.querySelector(".reduced").addEventListener("click",()=>{const newQuantity=parseInt(document.getElementById(`quantity-${item.id}`).value)-1;if(newQuantity>0){updateQuantity(item.id,newQuantity);}});row.querySelector(".delete-button").addEventListener("click",()=>{deleteCartItem(item.id);});tableBody.appendChild(row);});let totalP=document.getElementById('totalP')
totalP.textContent=cartItem.total_price}
function updateQuantity(itemId,newQuantity){const cartId=localStorage.getItem("cartId");fetch(`/shop/cart/${cartId}/items/${itemId}/`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({quantity:newQuantity})}).then(response=>{if(response.ok){fetchCartItems(cartId);}else{console.error("Failed to update quantity:",response.statusText);}}).catch(error=>console.error("Error updating quantity:",error));}
function deleteCartItem(itemId){const cartId=localStorage.getItem("cartId");fetch(`/shop/cart/${cartId}/items/${itemId}/`,{method:"DELETE"}).then(response=>{if(response.ok){fetchCartItems(cartId);}else{console.error("Failed to delete item:",response.statusText);}}).catch(error=>console.error("Error deleting item:",error));};
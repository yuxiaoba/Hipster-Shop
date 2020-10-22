
using System;
using System.Collections.Concurrent;
using System.Threading.Tasks;
using System.Linq;
using cartservice.interfaces;
using Hipstershop;
using CommandLine;
using System.Threading;

namespace cartservice.cartstore
{
    internal class CartStore : ICartStore
    {
        const string REDIS_ADDRESS = "REDIS_ADDR";

        private ICartStore cartStore;

        public CartStore()
        {

            // Set redis cache host (hostname+port)
            Console.WriteLine($"Reading redis cache address from environment variable {REDIS_ADDRESS}");
            string redis = Environment.GetEnvironmentVariable(REDIS_ADDRESS);
            // Redis was specified via command line or environment variable
            if (!string.IsNullOrEmpty(redis))
            {
                // If you want to start cart store using local cache in process, you can replace the following line with this:
                // cartStore = new LocalCartStore();
                cartStore = new RedisCartStore(redis);
            }
            else
            {
                Console.WriteLine("Redis cache host(hostname+port) was not specified. Starting a cart service using local store");
                Console.WriteLine("If you wanted to use Redis Cache as a backup store, you should provide its address via command line or REDIS_ADDRESS environment variable.");
                cartStore = new LocalCartStore();
            }
        }


        public Task AddItemAsync(string userId, string productId, int quantity)
        {
            return cartStore.AddItemAsync(userId, productId, quantity);
        }

        public Task EmptyCartAsync(string userId)
        {
            return cartStore.EmptyCartAsync(userId);
        }

        public Task<Cart> GetCartAsync(string userId)
        {
            return cartStore.GetCartAsync(userId);
        }

        public Task InitializeAsync()
        {
            return cartStore.InitializeAsync();
        }

        public bool Ping()
        {
            return cartStore.Ping();
        }
    }
}